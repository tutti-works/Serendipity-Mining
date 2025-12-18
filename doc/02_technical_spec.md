# Serendipity Mining - 技術仕様書

## 1. システムアーキテクチャ
### 1.1 全体構成
- Config Loader: YAML（domains / vocab / axis_templates）と環境変数を読み込み
- Data Manager: 500枚の生成計画を作成（基本480 + ミックス10 + リラン10）
- Prompt Generator: 軸テンプレートに文脈・語彙・ヒントを埋め込み
- API Client: `google-genai` で Gemini 画像生成を呼び出し
- Image Extractor: thinking画像を含むレスポンスから最終画像を特定し抽出
- Output Handler: 画像・JSON・manifest.jsonl を保存

### 1.2 コンポーネント詳細
- Config Loader: `domains.yaml` / `vocab.yaml` / `axis_templates.yaml` を読み込み、環境変数 `GOOGLE_API_KEY` を必須チェック
- Data Manager: 10軸×6束×8枚の組み合わせを作成し、ミックス/リラン枠を追加、manifest.jsonl から再開対象を判定
- Prompt Generator: 軸テンプレートに `{context}` と `{h1}/{h2}`（ドメインのヒント2語）および語彙を埋め込んで最終プロンプトを生成
- API Client: `genai.Client(api_key=...)` で初期化し、`client.models.generate_content` に `image_config=types.ImageConfig(image_size="2K")` を明示
- Image Extractor: `response.parts` を優先し、なければ `response.candidates[0].content.parts` をフォールバックとして参照
- Output Handler: 最終画像を `.png` で保存し、オプションで thinking 画像も保存。メタデータ JSON と manifest.jsonl に記録

---

## 2. 技術スタック
### 2.1 言語・ランタイム
- Python 3.10+

### 2.2 依存ライブラリ
```
google-genai>=1.0.0
pyyaml>=6.0
tqdm>=4.65
python-dotenv>=1.0
```

### 2.3 外部API
- Gemini API（AI Studio 経由）
- モデル: `gemini-3-pro-image-preview`
- 認証: `GOOGLE_API_KEY` のみ（Vertex AI / GOOGLE_APPLICATION_CREDENTIALS は使用しない）

---

## 3. ファイル構成
```
SerendipityMining/
├── run.py                 # エントリーポイント
├── requirements.txt       # 依存ライブラリ
├── .env                   # APIキー（git 管理外）
├── config/
│   └── config.yaml        # オプション設定
├── data/
│   ├── domains.yaml       # 30ドメイン定義
│   ├── vocab.yaml         # 語彙辞書
│   └── axis_templates.yaml # 10軸テンプレート
├── src/
│   ├── config_loader.py   # 設定読み込み
│   ├── data_manager.py    # 計画生成・再開判定
│   ├── prompt_generator.py # プロンプト生成
│   ├── api_client.py      # Gemini API 呼び出し
│   ├── image_extractor.py # 画像抽出（thinking対応）
│   └── output_handler.py  # 保存・manifest
├── out/                   # 出力先
└── doc/                   # ドキュメント
```

---

## 4. 処理フロー
1. 初期化: 環境変数読み込み、クライアント初期化、出力ディレクトリ作成
2. 生成計画作成: 480枚 + ミックス10枚 + リラン10枚。manifest.jsonl と plan.jsonl を参照してスキップ対象を決定
3. ループ（計500回）:
   - プロンプト生成（ヒント2語 + 文脈 + 語彙）
   - API呼び出し（指数バックオフ付きリトライ）
   - レスポンスから画像抽出（最後の画像パートを最終画像、1パートならそれを採用）
   - 画像/JSON保存、manifest 追記
4. 終了時にサマリ表示

---

## 5. SDK仕様とコード例（google-genai）
### 5.1 初期化
```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
```

### 5.2 画像生成
```python
from google.genai import types

def generate_image(prompt: str):
    return client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(image_size="2K"),
        ),
    )
```

### 5.3 レスポンスから画像抽出（thinking対応 + base64判定）
```python
import base64
from typing import Iterable

THINKING_RULE = "最後以外はthinking。画像パートが1つならそれを最終とする"  # 明示ルール

def iter_image_parts(response) -> Iterable:
    # response.parts を優先。なければ candidates[0].content.parts をフォールバック
    if getattr(response, "parts", None):
        return response.parts
    if getattr(response, "candidates", None):
        candidates = response.candidates or []
        if candidates and getattr(candidates[0], "content", None):
            return candidates[0].content.parts or []
    return []

def extract_images(response) -> dict:
    image_blobs = []
    for part in iter_image_parts(response):
        data = getattr(getattr(part, "inline_data", None), "data", None)
        mime = getattr(getattr(part, "inline_data", None), "mime_type", None)
        if not data or not mime or not mime.startswith("image/"):
            continue
        # data が bytes のときはそのまま、str のときのみ base64 デコード
        if isinstance(data, str):
            data = base64.b64decode(data)
        image_blobs.append(data)

    if not image_blobs:
        raise ValueError("No image data in response")

    if len(image_blobs) == 1:
        final_idx = 0
    else:
        final_idx = len(image_blobs) - 1  # 最後以外はthinking

    return {
        "final_image": image_blobs[final_idx],
        "final_image_index": final_idx,
        "thought_images": image_blobs[:final_idx],
        "total_parts": len(image_blobs),
    }
```

### 5.4 レスポンスメタデータ抽出
```python
def extract_response_metadata(response) -> dict:
    meta = {"finish_reason": None, "safety_ratings": None, "model_version": None}
    candidate = response.candidates[0] if getattr(response, "candidates", None) else None
    if candidate:
        if getattr(candidate, "finish_reason", None):
            meta["finish_reason"] = str(candidate.finish_reason)
        if getattr(candidate, "safety_ratings", None):
            meta["safety_ratings"] = [
                {
                    "category": str(r.category if not hasattr(r.category, "name") else r.category.name),
                    "probability": str(r.probability if not hasattr(r.probability, "name") else r.probability.name),
                }
                for r in candidate.safety_ratings
            ]
    if getattr(response, "model_version", None):
        meta["model_version"] = response.model_version
    return meta
```

### 5.5 リトライ（指数バックオフ）
```python
import time

def generate_with_retry(prompt: str, max_retries: int = 3, base_delay: float = 2.0):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return generate_image(prompt)
        except Exception as e:
            last_error = e
            err, _ = classify_error(e)
            if err in ("SAFETY_BLOCKED", "AUTH_ERROR"):
                raise
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
    return None
```

### 5.6 エラー分類
```python
def classify_error(exception) -> tuple[str, int | None]:
    msg = str(exception).lower()
    if "safety" in msg or "blocked" in msg:
        return ("SAFETY_BLOCKED", 400)
    if "rate" in msg or "quota" in msg or "resource_exhausted" in msg:
        return ("RATE_LIMITED", 429)
    if "authentication" in msg or "permission" in msg or "api_key" in msg:
        return ("AUTH_ERROR", 401)
    if "connection" in msg or "timeout" in msg:
        return ("CONNECTION_ERROR", None)
    if hasattr(exception, "status_code"):
        return ("API_ERROR", exception.status_code)
    if hasattr(exception, "code"):
        return ("API_ERROR", exception.code)
    return ("UNKNOWN_ERROR", None)
```

---

## 6. メタデータ仕様
- 画像と同名の `.json` に保存。`manifest.jsonl` にも同内容を1行ずつ追記。
- フィールドは `run_id, index, created_at, model, image_resolution, axis_id, bundle, domain_id, template_text, final_prompt, hints_used, vocab_used, generation_type, image_part_index, total_image_parts, is_thought, thought_images_saved, response_metadata, error, error_type, http_status, retry_count` を想定。

---

## 7. エラーハンドリング
- SAFETY_BLOCKED / AUTH_ERROR: 即停止またはスキップ（リトライしない）
- RATE_LIMITED / CONNECTION_ERROR / UNKNOWN: 指数バックオフで最大3回リトライ
- NO_IMAGE_DATA: 画像パートなし。メタデータに記録しスキップ

---

## 8. セキュリティ
- APIキーは `GOOGLE_API_KEY` でのみ管理し、`GOOGLE_APPLICATION_CREDENTIALS` や Vertex AI 設定は使わない（`google-genai` は `GEMINI_API_KEY` も読むが、本プロジェクトでは `GOOGLE_API_KEY` に統一）
- `.env` を `.gitignore` に含める
- 生成物にAPIキーや機密情報を含めない

---

## 9. パフォーマンスと再開
- tqdm で進捗表示
- plan.jsonl と manifest.jsonl で再開を O(1) 判定（セットで completed index を保持）
- 画像保存は逐次書き込みでメモリ圧を抑制

---

## 10. コストと解像度
- モデル: `gemini-3-pro-image-preview`、解像度は **2K固定**（config の `image_config.image_size="2K"` を必ず指定）
- 試作500枚: 画像コスト 約 $67、テキストコストは軽微
- 本番1,800枚: 画像コスト 約 $241
