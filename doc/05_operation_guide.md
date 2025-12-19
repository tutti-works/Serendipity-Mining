# Serendipity Mining - 運用ガイド（案A：slot固定 / profile切替）

## 1. セットアップ
### 1.1 環境
```bash
python --version  # 3.10+
python -m venv venv
./venv/Scripts/activate   # Windows
# source venv/bin/activate # Linux/Mac
pip install -r requirements.txt
```

### 1.2 APIキー
AI Studio で取得した API キーを `.env` に設定（GOOGLE_API_KEY のみ使用）。
```bash
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```

### 1.3 データ
プロファイルごとに `profiles/{profile}/axis_templates.yaml` と `vocab.yaml` を用意（bundle/domain は使用しない）。

---

## 2. 実行方法
### 2.1 基本
```bash
python run.py --profile 3labs
python run.py --profile 4cats
```

### 2.2 プロファイル切替と plan 切替
- 出力は `out/{profile}/images/{axis_id}/...` と `out/{profile}/meta/{axis_id}/...`
- plan/manifest は `out/{profile}/{plan_name}.jsonl` / `out/{profile}/manifest.jsonl`

探索用と本番用を分ける例:
```bash
# 探索 plan を生成（再生成強制、seed はこの時だけ効く）
python run.py --profile 4cats --plan-name explore --regen-plan --seed 123 --dry-run --count 10
# 同じ探索 plan を再利用（seed を指定しても既存 plan を優先）
python run.py --profile 4cats --plan-name explore --dry-run --count 10
# 本番 plan（軸ウェイトを調整してから再生成）
python run.py --profile 4cats --plan-name prod --regen-plan --exclude-plan explore --seed 123 --dry-run --count 10
```

### 2.3 パラメータ
- `--plan-name`: 使う plan ファイル名（拡張子不要、デフォルト `plan`）
- `--regen-plan`: 既存 plan があっても再生成する
- `--seed`: plan 新規生成時のみ使用（既存 plan を再利用する場合は無視される）
- `--count`: plan 先頭から N 件だけ実行（dry-run で内容確認に便利）

### 2.4 件数とウェイト
profiles/{profile}/config.yaml で制御:
- `target_count`: 生成件数
- `axis_weights`: 軸ごとの比率（合計1.0目安、未指定なら均等）
- `dedupe_mode`: `strict`（同一 slots を重複させない）/`soft`
- `global_prompt_suffix`: 全プロンプトに末尾付与（例: `single main subject, minimal clutter...`）
- `tag_sampling`: タグ付き vocab のサンプリング方法（uniform/weighted/off をカテゴリごとに設定可能）
- `sampling_controls`: `max_repeat_window` / `max_repeat_per_token` で直近/全体の重複を抑制

### 2.5 ドメイン注入
`domain_injection` = `none` / `context` / `context_and_hints`  
案Aでは `none`（bundle/domain 不使用）でシンプルなプロンプトを維持。

### 2.6 再開
manifest の `status=success` のみスキップして再開。途中で止まっても同じコマンドで再開可能。

---

## 3. 出力確認
```bash
dir out/{profile}/images
tail -n 5 out/{profile}/manifest.jsonl
```
メタ JSON/manifest には `profile, plan_name, axis_id, slots, final_prompt, status, error, image_size` が入る。

---

## 4. 運用フロー（推奨）
1. 探索: 少数枚・均等ウェイトで `--plan-name explore --regen-plan --seed ...`
2. 評価: 当たり軸を確認し、axis_weights を更新
3. 本番: `--plan-name prod --regen-plan --seed ...` で本番 plan を確定
4. 公平比較: seed ではなく固定 plan（explore/prod）で比較

---

## 5. vocab 推奨数（最低ライン）
- MATERIAL / OBJECT / LOCATION / ERA_STYLE / ADJ_STATE / NOUN: 最低50、推奨150〜300
- 4cats 追加: TECH_THING 150〜300, ABSTRACT_CONCEPT 100〜250, CONCRETE_THING 150〜300, SUBJECT_A/SUBJECT_B 150〜300, SCALE 20〜40
- 形式は snake_case、重複・長文・引用符は避ける（画像内テキスト誘発を防止）

### 5.1 vocab フォーマット例（サブタグ/_weights 対応）
旧形式（リストのみ）と新形式（タグ分割＋_weights）を両対応:
```yaml
OBJECT:
  - sneaker
  - glass_beaker
OBJECT:
  _weights:
    everyday: 2.0
    industrial: 1.0
  everyday:
    - sneaker
    - coffee_mug
  industrial:
    - circuit_board
    - valve_handle
```

### 5.2 サンプリング設定
```yaml
tag_sampling:
  mode: uniform            # default forカテゴリ未指定
  per_category:
    OBJECT: uniform        # uniform | weighted | off
    MATERIAL: uniform
    SUBJECT_A: uniform
    SUBJECT_B: uniform
    TECH_THING: uniform
    CONCRETE_THING: uniform
    ERA_STYLE: off
    ABSTRACT_CONCEPT: off
    SCALE: off
sampling_controls:
  max_repeat_window: 200   # 直近windowで同一tokenをなるべく避ける（試み）
  max_repeat_per_token: 8  # plan全体での繰り返し上限（超えると警告）
```

### 5.3 増量ルール（質重視）
- 禁止: 固有名詞、長すぎる snake_case、logo/typography/poster など文字を誘発する語、thing/object/stuff など曖昧語
- 推奨: 視覚特徴が強い名詞、素材は質感が異なるものを分散、抽象は絵にしやすい概念を優先
- 重複抑制: 同じstemの乱造を避け、タグで分けて均等サンプリング

---

## 6. トラブルシュート
- `AUTH_ERROR`: `.env` のキーを確認
- `NO_IMAGE_DATA`: プロンプトとレスポンスを確認、再実行
- plan/manifest 破損時: バックアップを取り、`--regen-plan` で再生成

---

## 7. チェックリスト
- [ ] GOOGLE_API_KEY を設定
- [ ] profile の vocab が十分（推奨数以上）
- [ ] `target_count` と `axis_weights` が意図どおり
- [ ] dry-run で {PLACEHOLDER} 残りがないことを確認

---

## 8. Gemini Batch 運用
### 8.1 CLI
```bash
# 提出（chunk分割。既存jobsがある場合は --batch-force-submit で再投入）
python run.py --profile 4cats --plan-name prod --mode batch --batch-action submit --batch-chunk-size 300
# 状態確認
python run.py --profile 4cats --plan-name prod --mode batch --batch-action status
# 回収（完了済みのみcollectし、画像/meta/manifestに反映）
python run.py --profile 4cats --plan-name prod --mode batch --batch-action collect
```
- `--mode batch` は Gemini Batch API 専用（Vertex Batch ではない）。
- `--batch-mime-type` はアップロード失敗時に `text/plain` などへ切り替え可能。
- 入力JSONL 1行のスキーマ: `{"key": "<profile>:<plan_name>:<index>", "request": <GenerateContentRequest>}`  
  `key` は chunk 跨ぎでも一意。

### 8.2 ファイル制約と運用
- input JSONL は 1ファイル最大2GB、プロジェクト合計20GB、保持48時間。  
  -> `--batch-chunk-size` はデフォルト300。出力肥大化を避けるため状況に応じて調整。
- `submit` 後は 48時間以内に `collect`。失効したら再submitが必要。
- jobs記録: `out/{profile}/batches/{plan_name}.jobs.jsonl` に `profile, plan_name, chunk_id, index_range, input_jsonl_path, uploaded_file_name, batch_name, created_at, model, mime_type` を追記。
- 非idempotentのため、jobsがある chunk はデフォルト再submitしない。`--batch-force-submit` を付けると二重生成の恐れがあることをログで明示。

### 8.3 collect の挙動と安全策
- 出力JSONLはストリーミング処理（全件をメモリに載せない）。
- `key` から index を復元し、plan と突合して保存先を決定。
- 既に `status=success` のものは上書きせずスキップ（ログのみ）。
- 成功: 画像保存 + meta/manifest を `status=success` で追記。  
  失敗: meta/manifest に `status=failed` / `error` を記録（次回再実行で拾える）。
- collect 後にサマリを表示（success/failed/pending）。

### 8.4 トラブルシュート
- upload失敗: `--batch-mime-type text/plain` を試す。
- 出力参照なし: batch の state が `SUCCEEDED/COMPLETED` か確認。
- 48時間超過: inputファイル失効の可能性。planを変えずに再submit。

---

## 9. tools スクリプトの使い方
### 9.1 語彙監査（vocab_audit）
```bash
python tools/vocab_audit.py profiles/4cats/vocab.yaml
```
- snake_case準拠、重複、禁止語、カテゴリ件数の警告を表示。

### 9.2 偏りチェック（bias_report）
```bash
python tools/bias_report.py out/4cats/explore.jsonl
python tools/bias_report.py out/4cats/explore.jsonl --top 20
```
- axis分布、slot_tags分布、トークン頻度（top N）を出力。

### 9.3 plan重複チェック（check_overlap）
```bash
python tools/check_overlap.py out/4cats/explore.jsonl out/4cats/prod.jsonl
```
- axis_id + slots の重複数を表示（被り0の確認用）。
