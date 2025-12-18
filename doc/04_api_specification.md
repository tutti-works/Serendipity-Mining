# Serendipity Mining - Gemini API仕様書

## 1. 概要
本システムは Google Gen AI SDK（`google-genai`）を用いて Gemini 画像生成 API を呼び出す。認証は AI Studio APIキー（環境変数 `GOOGLE_API_KEY`）のみを使用し、Vertex AI や `GOOGLE_APPLICATION_CREDENTIALS` は使わない。

- モデル: **`gemini-3-pro-image-preview`**（固定）
- 解像度: **2K固定**（`image_config=types.ImageConfig(image_size="2K")` を config で必ず指定）
- レスポンス: 画像パートを複数返すことがあり、thinking 画像は最後以外。画像パートが1つの場合はそれを最終画像とみなす。

---

## 2. モデル仕様
| 項目 | 値 |
|------|-----|
| モデル名 | gemini-3-pro-image-preview |
| 種別 | プレビュー画像モデル |
| 入力コンテキスト長 | 約 65k tokens |
| 出力コンテキスト長 | 約 32k tokens |
| 知識カットオフ | 2025年1月 |
| 対応入力 | テキスト, 画像（PNG/JPEG）|
| 推奨解像度 | **2K**（本プロジェクト固定）|

---

## 3. 料金の目安（2K固定）
| 生成枚数 | 画像コスト | テキストコスト | 合計概算 |
|---------|---------|-------------|----------|
| 500枚 | 約 $67 | 約 $0.20 | **約 $70** |
| 1,800枚 | 約 $241 | 約 $0.72 | **約 $245** |

※ 画像単価は約 $0.134 / 枚（2K）。

---

## 4. 認証と SDK
### 4.1 インストール
```bash
pip install google-genai
```

### 4.2 認証・初期化
```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
```
`GOOGLE_API_KEY` 以外の認証手段は使用しない。

---

## 5. 画像生成 API 呼び出し
### 5.1 最低限の呼び出し例
```python
from google.genai import types

response = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(image_size="2K"),
    ),
)
```

### 5.2 リトライ付きの推奨ラッパ
```python
import time

def generate_with_retry(prompt: str, max_retries: int = 3, base_delay: float = 2.0):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(image_size="2K"),
                ),
            )
        except Exception as e:
            last_error = e
            kind, _ = classify_error(e)
            if kind in ("SAFETY_BLOCKED", "AUTH_ERROR"):
                raise
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
    return None
```

---

## 6. 画像抽出ポリシー（thinking対応 + base64ガード）
### 6.1 ルール
- 画像パートが複数ある場合: 「最後の画像パート」を最終画像とし、最後以外は thinking 画像。
- 画像パートが1つだけの場合: thinking が返らないケースとしてそれを最終画像とする。
- `inline_data.data` が bytes ならそのまま保存、str の場合のみ base64 デコードして保存。
- 取得元は `response.parts` を優先し、なければ `response.candidates[0].content.parts` をフォールバック。

### 6.2 抽出コード例
```python
import base64
from typing import Iterable

THINKING_RULE = "最後以外はthinking。1パートならそれを最終とする"

def iter_parts(resp) -> Iterable:
    if getattr(resp, "parts", None):
        return resp.parts
    if getattr(resp, "candidates", None):
        cands = resp.candidates or []
        if cands and getattr(cands[0], "content", None):
            return cands[0].content.parts or []
    return []

def extract_images(resp) -> dict:
    images = []
    for part in iter_parts(resp):
        data = getattr(getattr(part, "inline_data", None), "data", None)
        mime = getattr(getattr(part, "inline_data", None), "mime_type", None)
        if not data or not mime or not mime.startswith("image/"):
            continue
        if isinstance(data, str):
            data = base64.b64decode(data)
        images.append(data)

    if not images:
        raise ValueError("No image data in response")

    final_idx = 0 if len(images) == 1 else len(images) - 1
    return {
        "final_image": images[final_idx],
        "final_image_index": final_idx,
        "thought_images": images[:final_idx],
        "total_parts": len(images),
    }
```

---

## 7. レスポンスメタデータ
```python
def extract_response_metadata(resp) -> dict:
    meta = {"finish_reason": None, "safety_ratings": None, "model_version": None}
    cand = resp.candidates[0] if getattr(resp, "candidates", None) else None
    if cand:
        if getattr(cand, "finish_reason", None):
            meta["finish_reason"] = str(cand.finish_reason)
        if getattr(cand, "safety_ratings", None):
            meta["safety_ratings"] = [
                {
                    "category": str(r.category if not hasattr(r.category, "name") else r.category.name),
                    "probability": str(r.probability if not hasattr(r.probability, "name") else r.probability.name),
                }
                for r in cand.safety_ratings
            ]
    if getattr(resp, "model_version", None):
        meta["model_version"] = resp.model_version
    return meta
```

---

## 8. エラーハンドリング
| 種別 | 検知方法 | 対応 |
|------|---------|------|
| SAFETY_BLOCKED | メッセージに "safety" または "blocked" | リトライせずスキップ/停止 |
| RATE_LIMITED | "rate" / "quota" / "resource_exhausted" | 指数バックオフでリトライ |
| AUTH_ERROR | "authentication" / "permission" / "api_key" | 即停止 |
| CONNECTION_ERROR | "connection" / "timeout" | 指数バックオフでリトライ |
| API_ERROR/UNKNOWN | その他 | 最大3回リトライ後スキップ |

分類関数:
```python
def classify_error(e) -> tuple[str, int | None]:
    msg = str(e).lower()
    if "safety" in msg or "blocked" in msg:
        return ("SAFETY_BLOCKED", 400)
    if "rate" in msg or "quota" in msg or "resource_exhausted" in msg:
        return ("RATE_LIMITED", 429)
    if "authentication" in msg or "permission" in msg or "api_key" in msg:
        return ("AUTH_ERROR", 401)
    if "connection" in msg or "timeout" in msg:
        return ("CONNECTION_ERROR", None)
    if hasattr(e, "status_code"):
        return ("API_ERROR", e.status_code)
    if hasattr(e, "code"):
        return ("API_ERROR", e.code)
    return ("UNKNOWN_ERROR", None)
```

---

## 9. 実装リファレンス（抜粋）
```python
from pathlib import Path
from datetime import datetime

prompt = "A product photo of 'chair' made entirely of 'molten_glass'."
resp = generate_with_retry(prompt)
if resp is None:
    raise RuntimeError("All retries failed")

extracted = extract_images(resp)
meta = extract_response_metadata(resp)

out_dir = Path("./out/material_paradox/bio_medical/operating_room")
out_dir.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
base = f"{ts}_0001_material_paradox_bio_medical_operating_room"

# 最終画像
with open(out_dir / f"{base}.png", "wb") as f:
    f.write(extracted["final_image"])
# thinking画像（任意）
for i, img in enumerate(extracted["thought_images"], start=1):
    with open(out_dir / f"{base}_thought_{i:02d}.png", "wb") as f:
        f.write(img)
```

---

## 10. 留意点
- 解像度は常に `image_size="2K"` を指定する。コメントだけで済ませず config で明示する。
- thinking 画像の有無はモデルからの保証がないため、画像パートが1つしかない場合のガードを必ず入れる。
- 画像抽出は `response.parts` を基本とし、フォールバックとして `response.candidates[0].content.parts` を参照する。
- `inline_data.data` の型が bytes か str かを判定し、str のときのみ base64 デコードする。
