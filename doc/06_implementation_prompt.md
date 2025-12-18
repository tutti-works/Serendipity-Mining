# コーディングAI向け実装指示書

以下はPythonエンジニア向けの実装指示。`doc/03_data_structure.md` も併読すること。

---

## 技術仕様サマリ
| 項目 | 値 |
|------|-----|
| SDK | `google-genai`（google-generativeai / google.generativeai は使用しない） |
| モデル | `gemini-3-pro-image-preview` 固定 |
| 解像度 | 2K 固定（`image_config.image_size="2K"` を config で指定） |
| 認証 | AI Studio APIキー（環境変数 `GOOGLE_API_KEY` のみ） |
| リトライ | 最大3回、指数バックオフ 2s -> 4s -> 8s |
| thinking画像 | 最後以外は thinking。画像パートが1つならそれを最終画像とみなす |

---

## 1. 目的
定義済みデータ構造（domains/vocab/axis templates）を使って **500枚** の画像を生成し、ローカルに保存・記録する。

---

## 2. 依存関係
### requirements.txt
```
google-genai>=1.0.0
pyyaml>=6.0
tqdm>=4.65
python-dotenv>=1.0
```

### インストール
```bash
pip install -r requirements.txt
```

---

## 3. 認証（AI Studio APIキーのみ）
```python
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
```
> Vertex AI / `GOOGLE_APPLICATION_CREDENTIALS` は使わない。

---

## 4. 入力データ
- `data/domains.yaml`: 30ドメイン（bundle, domain_id, context, hints）
- `data/vocab.yaml`: 語彙辞書（カテゴリ別）
- `data/axis_templates.yaml`: 10軸のテンプレート

---

## 5. 生成ルール（500枚）
- 基本生成 480枚: 10軸 x 6束 x 8枚（各束内の5ドメインを8回でラウンドロビン/等重みで均等に走査）
- ミックス枠 10枚: 2軸のテンプレートを結合し 500-800 文字に抑える
- リラン枠 10枚: 基本生成から10条件を選び、同一条件を seed 明示なしで再実行（分散確認用）
- ヒントは各ドメインの `hints` から **2語のみ** 抽選して `{h1}`, `{h2}` にセット
- `context` は必ずプロンプトに含める

---

## 6. Thinking画像の扱いと画像抽出
### 6.1 ルール
- 複数画像パート: 最後の画像パートを最終画像、最後以外は thinking
- 画像パートが1つ: thinking が無いケースとしてそれを最終画像とする
- `inline_data.data` が bytes の場合はそのまま保存、str の場合のみ base64 デコード
- 画像取得元は `response.parts` を基本とし、フォールバックで `response.candidates[0].content.parts` を参照

### 6.2 実装例
```python
import base64
from typing import Iterable

THINKING_RULE = "最後以外はthinking。1パートならそれを最終画像"  # ガード明記

def iter_image_parts(response) -> Iterable:
    if getattr(response, "parts", None):
        return response.parts
    if getattr(response, "candidates", None):
        cands = response.candidates or []
        if cands and getattr(cands[0], "content", None):
            return cands[0].content.parts or []
    return []

def extract_images_from_response(response) -> dict:
    images = []
    for part in iter_image_parts(response):
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

## 7. 出力構造とメタデータ
```
./out/{axis_id}/{bundle}/{domain_id}/
  {ts}_{index:04d}_{axis_id}_{bundle}_{domain_id}.png
  {ts}_{index:04d}_{axis_id}_{bundle}_{domain_id}.json
  {ts}_{index:04d}_{axis_id}_{bundle}_{domain_id}_thought_01.png  # 任意
manifest.jsonl  # 上記と同フィールドを1行ずつ追記
plan.jsonl      # 500件の生成計画（再開用）
```
メタデータに含める項目（必須）: `run_id, index, created_at, model, image_resolution(2K), axis_id, bundle, domain_id, template_text, final_prompt, hints_used, vocab_used, generation_type, image_part_index, total_image_parts, is_thought, thought_images_saved, response_metadata, error, error_type, http_status, retry_count`。

---

## 8. API呼び出し
### 8.1 基本関数
```python
from google.genai import types

def generate_image(client, prompt: str):
    return client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(image_size="2K"),
        ),
    )
```

### 8.2 リトライ
```python
import time

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

def generate_with_retry(client, prompt: str, max_retries: int = 3, base_delay: float = 2.0):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return generate_image(client, prompt), None
        except Exception as e:
            last_error = e
            err, status = classify_error(e)
            if err in ("SAFETY_BLOCKED", "AUTH_ERROR"):
                return None, (err, status, str(e))
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
    err, status = classify_error(last_error)
    return None, (err, status, str(last_error))
```

### 8.3 レスポンスメタデータ
```python
def extract_response_metadata(response) -> dict:
    meta = {"finish_reason": None, "safety_ratings": None, "model_version": None}
    cand = response.candidates[0] if getattr(response, "candidates", None) else None
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
    if getattr(response, "model_version", None):
        meta["model_version"] = response.model_version
    return meta
```

---

## 9. プロンプト生成
### 9.1 軸→プレースホルダ対応
```python
AXIS_PLACEHOLDERS = {
    "synesthesia": ["SENSATION", "SUBJECT"],
    "biomimicry": ["OBJECT", "BIO_STRUCTURE"],
    "literal_interpretation": ["IDIOM"],
    "macro_micro": ["SUBJECT"],
    "material_paradox": ["OBJECT", "MATERIAL_OR_STATE"],
    "glitch_contradiction": ["STYLE_A", "STYLE_B", "SUBJECT"],
    "affordance_inversion": ["THING", "WRONG_FUNCTION"],
    "representation_shift": ["SUBJECT"],
    "manufacturing_first": ["OBJECT", "CONSTRAINT"],
    "procedural_rules": ["RULESET", "SUBJECT"],
}
```

### 9.2 プロンプト組み立て
```python
import random

def build_prompt(axis_id, axis_templates, domain, vocab) -> tuple[str, dict]:
    t = axis_templates[axis_id]
    template = t["template"]
    hints = random.sample(domain["hints"], 2)
    placeholders = AXIS_PLACEHOLDERS[axis_id]
    vocab_used = {p: random.choice(vocab[p]) for p in placeholders}
    prompt = template.format(context=domain["context"], h1=hints[0], h2=hints[1], **vocab_used)
    return prompt, {
        "template_text": template,
        "hints_used": hints,
        "vocab_used": vocab_used,
    }
```

---

## 10. 生成計画
```python
AXIS_IDS = [
    "synesthesia", "biomimicry", "literal_interpretation", "macro_micro",
    "material_paradox", "glitch_contradiction", "affordance_inversion",
    "representation_shift", "manufacturing_first", "procedural_rules",
]
BUNDLE_IDS = [
    "bio_medical", "food_scent_chem", "legal_finance",
    "infra_industrial", "ritual_backstage", "human_ops",
]

def create_generation_plan(domains_by_bundle: dict):
    plan = []
    idx = 0
    # 各束でドメインをシャッフルして8回ラウンドロビン
    for axis_id in AXIS_IDS:
        for bundle in BUNDLE_IDS:
            domains = list(domains_by_bundle[bundle])
            random.shuffle(domains)
            for i in range(8):
                domain = domains[i % len(domains)]
                plan.append({
                    "index": idx,
                    "axis_id": axis_id,
                    "bundle": bundle,
                    "domain_id": domain["domain_id"],
                    "generation_type": "standard",
                })
                idx += 1
    # ミックス枠（軸IDは slug 化）
    for _ in range(10):
        pair = random.sample(AXIS_IDS, 2)
        plan.append({
            "index": idx,
            "axis_id": f"mix__{pair[0]}__{pair[1]}",
            "bundle": random.choice(BUNDLE_IDS),
            "generation_type": "mix",
            "axis_pair": pair,
        })
        idx += 1
    # リラン枠（同一 final_prompt を再実行）
    reruns = random.sample(plan[:480], 10)
    for src in reruns:
        plan.append({
            "index": idx,
            "axis_id": src["axis_id"],
            "bundle": src["bundle"],
            "domain_id": src.get("domain_id"),
            "generation_type": "rerun",
            "source_index": src["index"],
        })
        idx += 1
    return plan
```

---

## 11. メイン処理フロー（擬似コード）
```python
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

def load_plan(path: Path, domains_by_bundle):
    if path.exists():
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    plan = create_generation_plan(domains_by_bundle)
    path.write_text("\n".join(json.dumps(p, ensure_ascii=False) for p in plan), encoding="utf-8")
    return plan

def main():
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    domains = load_yaml("data/domains.yaml")["domains"]
    vocab = load_yaml("data/vocab.yaml")["vocab"]
    axis_templates = load_yaml("data/axis_templates.yaml")["axis_templates"]

    domains_by_bundle = {}
    for d in domains:
        domains_by_bundle.setdefault(d["bundle"], []).append(d)

    plan_path = Path("./out/plan.jsonl")
    plan = load_plan(plan_path, domains_by_bundle)
    completed = load_completed_indices("./out/manifest.jsonl")
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path("./out")

    # source_index -> final_prompt キャッシュ（manifest を読む）
    manifest_cache = load_manifest_by_index("./out/manifest.jsonl")

    for item in tqdm(plan, desc="Generating images"):
        idx = item["index"]
        if idx in completed:
            continue
        bundle = item["bundle"]
        domain_list = domains_by_bundle[bundle]
        domain = next((d for d in domain_list if d["domain_id"] == item.get("domain_id")), None)
        if domain is None:
            raise ValueError(f"domain not found for bundle={bundle}, domain_id={item.get('domain_id')}")

        if item["generation_type"] == "rerun":
            source_meta = manifest_cache.get(item["source_index"])
            if not source_meta:
                raise ValueError(f"source manifest missing for rerun index {item['source_index']}")
            prompt = source_meta["final_prompt"]
            prompt_meta = {
                "template_text": source_meta.get("template_text"),
                "hints_used": source_meta.get("hints_used"),
                "vocab_used": source_meta.get("vocab_used"),
            }
        elif item["generation_type"] == "mix":
            prompt, prompt_meta = build_mix_prompt(item["axis_pair"], axis_templates, domain, vocab)
        else:
            prompt, prompt_meta = build_prompt(item["axis_id"], axis_templates, domain, vocab)

        response, error_info = generate_with_retry(client, prompt)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{ts}_{idx:04d}_{item['axis_id']}_{bundle}_{domain['domain_id']}"
        img_dir = output_dir / item["axis_id"] / bundle / domain["domain_id"]

        metadata = {
            "run_id": run_id,
            "index": idx,
            "created_at": datetime.now().isoformat(),
            "model": "gemini-3-pro-image-preview",
            "image_resolution": "2K",
            "axis_id": item["axis_id"],
            "bundle": bundle,
            "domain_id": domain["domain_id"],
            "final_prompt": prompt,
            "generation_type": item["generation_type"],
            **prompt_meta,
        }

        if error_info:
            err, status, msg = error_info
            metadata |= {
                "image_part_index": None,
                "total_image_parts": None,
                "is_thought": None,
                "thought_images_saved": [],
                "response_metadata": None,
                "error": msg,
                "error_type": err,
                "http_status": status,
                "retry_count": 3 if err not in ("SAFETY_BLOCKED", "AUTH_ERROR") else 0,
            }
        else:
            try:
                extracted = extract_images_from_response(response)
                resp_meta = extract_response_metadata(response)
                saved = save_images(extracted, img_dir, base, save_thoughts=True)
                metadata |= {
                    "image_part_index": extracted["final_image_index"],
                    "total_image_parts": extracted["total_parts"],
                    "is_thought": False,
                    "thought_images_saved": [Path(p).name for p in saved.get("thoughts", [])],
                    "response_metadata": resp_meta,
                    "error": None,
                    "error_type": None,
                    "http_status": None,
                    "retry_count": 0,
                }
            except ValueError as e:
                metadata |= {
                    "image_part_index": None,
                    "total_image_parts": None,
                    "is_thought": None,
                    "thought_images_saved": [],
                    "response_metadata": extract_response_metadata(response),
                    "error": str(e),
                    "error_type": "NO_IMAGE_DATA",
                    "http_status": None,
                    "retry_count": 0,
                }

        save_metadata(img_dir, base, metadata)
        append_to_manifest(output_dir / "manifest.jsonl", metadata)
        manifest_cache[idx] = metadata  # rerun 用キャッシュ更新
```

補助関数 `save_images`, `load_yaml`, `load_completed_indices`, `append_to_manifest`, `save_metadata`, `load_manifest_by_index` を実装する。`load_manifest_by_index` は manifest.jsonl を読み、index -> メタデータ辞書を返す。

---

## 12. チェックリスト
- [ ] SDK は `google-genai` を使用し、`genai.Client(api_key=...)` で初期化している
- [ ] モデル名が `gemini-3-pro-image-preview` で固定されている
- [ ] config に `image_config=types.ImageConfig(image_size="2K")` を明記している
- [ ] 認証は `GOOGLE_API_KEY` のみを参照し、Vertex AI/サービスアカウントを使っていない
- [ ] thinking 画像ルール（最後以外 / 1パートならそれを最終）を実装し、メタデータに `image_part_index`, `total_image_parts`, `is_thought` を記録している
- [ ] `inline_data.data` の bytes/str を判定し、str の場合のみ base64 デコードしている
- [ ] hints を毎回2語だけ使用し、context を必ずプロンプトに含めている
- [ ] 画像と同名の JSON を保存し、manifest.jsonl に全レコードを追記している
- [ ] plan.jsonl を保存・再利用し、生成順序が再開時に揺れない
- [ ] rerun は source_index の final_prompt を再利用して呼び直している
- [ ] 最大3回の指数バックオフリトライが組み込まれている
