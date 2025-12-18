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
python run.py --profile 3labs --plan-name explore --regen-plan --seed 123 --dry-run --count 10
# 同じ探索 plan を再利用（seed を指定しても既存 plan を優先）
python run.py --profile 3labs --plan-name explore --dry-run --count 10
# 本番 plan（軸ウェイトを調整してから再生成）
python run.py --profile 3labs --plan-name prod --regen-plan --seed 123 --dry-run --count 10
```
4cats も同様に `--profile 4cats` で実行可能。

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
