# Serendipity Mining - 運用ガイド

## 1. セットアップ
### 1.1 環境準備
```bash
python --version  # 3.10+ を確認
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
./venv/Scripts/activate
```

### 1.2 依存関係インストール
```bash
pip install -r requirements.txt
```
`requirements.txt`（抜粋）:
```
google-genai>=1.0.0
pyyaml>=6.0
tqdm>=4.65
python-dotenv>=1.0
```

### 1.3 APIキー設定（AI Studio）
1. https://aistudio.google.com/app/apikey で APIキーを取得
2. `.env` を作成しキーを格納（git 管理外）
```bash
echo "GOOGLE_API_KEY=your-api-key-here" > .env
```
- Vertex AI やサービスアカウントは使わない
- `GOOGLE_APPLICATION_CREDENTIALS` は設定しない

### 1.4 データファイル配置
```
SerendipityMining/
├── data/
│   ├── domains.yaml
│   ├── vocab.yaml
│   └── axis_templates.yaml
└── doc/03_data_structure.md を参照
```

---

## 2. 実行方法
### 2.1 基本
```bash
python run.py
```

### 2.2 オプション例（実装している場合）
```bash
python run.py --count 100            # 生成枚数指定
python run.py --output ./my_output   # 出力先指定
python run.py --dry-run              # API呼び出しなし
python run.py --axis material_paradox
python run.py --bundle bio_medical
python run.py --no-save-thoughts     # thinking 画像を保存しない
```
（上記オプションを使わない実装の場合は、ドキュメントから削除するか、ヘルプに反映してください。）

### 2.3 再開
途中停止後に同じコマンドを実行すると、初回保存した `plan.jsonl`（500件の固定計画）を読み込み、`manifest.jsonl` にある index をスキップして再開する。計画が変わらないことで再開時のズレを防ぐ。

---

## 3. 出力確認
### 3.1 ディレクトリ構造
```
./out/
├── synesthesia/
│   ├── bio_medical/
│   │   ├── operating_room/
│   │   │   ├── 20240115_123456_0001_synesthesia_bio_medical_operating_room.png
│   │   │   ├── 20240115_123456_0001_synesthesia_bio_medical_operating_room.json
│   │   │   └── 20240115_123456_0001_synesthesia_bio_medical_operating_room_thought_01.png  # 任意
│   │   └── ...
├── manifest.jsonl
└── plan.jsonl       # 500件の生成計画（再開用）
```

### 3.2 メタデータ確認
```bash
# 個別JSON
cat ./out/synesthesia/bio_medical/operating_room/20240115_123456_0001_*.json | jq .
# manifest末尾
tail -10 ./out/manifest.jsonl | jq .
# 軸別件数
grep '"axis_id":"material_paradox"' ./out/manifest.jsonl | wc -l
# エラーのみ
grep '"error_type"' ./out/manifest.jsonl | grep -v 'null' | jq .
```

---

## 4. 評価プロセス（試作500枚）
1. 500枚生成
2. 画像を確認し?評価（最終画像のみ、`*_thought_*` は評価対象外）
3. 評価をCSV等に記録
4. 軸/束ごとに集計し当たり軸・当たり束を特定
5. 本番配分を決定（例: 当たり軸に追加投資）

評価シート例:
```csv
index,axis_id,bundle,domain_id,rating,total_image_parts,notes
1,synesthesia,bio_medical,operating_room,2,3,色の組み合わせが独特
2,biomimicry,food_scent_chem,molecular_gastronomy,1,1,構造は良いが色が平凡
```

---

## 5. トラブルシューティング
- **AUTH_ERROR**: `.env` のキーを確認、キーの有効性を再確認
- **RATE_LIMITED**: 自動リトライで解消しない場合は実行間隔を広げる
- **SAFETY_BLOCKED**: 該当プロンプト/語彙の組み合わせを見直す
- **NO_IMAGE_DATA**: 画像パートが無い。プロンプトの記載ミスが無いか確認
- **ファイル書き込みエラー**: 出力先の権限を確認
- plan/manifest が破損した場合はバックアップを取り、必要に応じて再生成する（plan.jsonl は固定計画のため上書きしない）。

---

## 6. ベストプラクティス
1. 小さく始める（まず50枚程度で疎通確認）
2. ログと manifest を定期的に確認し、エラー傾向を早期に把握
3. `./out/` は定期バックアップ
4. thinking 画像の有無を確認し、最終画像と混同しないこと（最後のパートを最終画像、1パートならそれを採用）
5. 依存: `google-genai` に統一。`google-generativeai / google.generativeai` は使用しない。
6. 生成解像度は `image_size="2K"` を config で必ず指定し、コメントのみで済ませない。

---

## 7. コスト管理（2K固定）
```
試作 500枚: 約 $67 + テキスト微小 ? $70
本番 1800枚: 約 $241 + テキスト微小 ? $245
```
- AI Studio の利用状況で使用量を確認
- 予算アラートを設定（推奨）

---

## 8. 運用チェックリスト
### 8.1 生成前
- [ ] `GOOGLE_API_KEY` が `.env` に設定済みで有効
- [ ] data ファイル（domains/vocab/axis_templates）が揃っている
- [ ] plan.jsonl が存在する（なければ初回実行で生成）
- [ ] 試し生成（数枚）が成功
- [ ] 解像度指定 `image_size="2K"` をコードで明示

### 8.2 生成中
- [ ] エラー率が異常に高くなっていない
- [ ] 出力が正しく保存されている
- [ ] thinking 画像がある場合でも最後のパートのみ最終保存できている

### 8.3 生成後
- [ ] 総生成枚数が計画と一致
- [ ] manifest.jsonl が欠損なく更新されている
- [ ] 最終画像が誤って thinking に置き換わっていない
- [ ] plan.jsonl と出力をバックアップしている
