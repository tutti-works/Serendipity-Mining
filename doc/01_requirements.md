# Serendipity Mining - 要件定義書

## 1. プロジェクト概要
### 1.1 プロジェクト名
Serendipity Mining（セレンディピティ・マイニング）
### 1.2 目標
AI画像生成を活用し「偶然の発見（セレンディピティ）」を体系的に引き出す画像生成システムを構築する。人間の発想ルートを意図的に揺らし、予期しない創造的アウトプットを大量生成・評価・最適化する。
### 1.3 背景
- 従来の画像生成は既知の領域に収束しやすい
- 探索空間を広げることでセレンディピティを最大化したい
- 軸（生成オペレータ）とドメイン（語彙領域）を掛け合わせて多様性を担保する

---

## 2. 機能要件

### 2.1 画像生成
#### 2.1.1 基本生成
- **10軸 × 6束 × 8枚 = 480枚** を標準生成
- 各生成で軸テンプレート + ドメイン文脈 + 語彙を組み合わせてプロンプト生成
- **モデル**: `gemini-3-pro-image-preview`
- **解像度**: 2K固定（`image_size="2K"` を config で指定）
- **SDK**: `google-genai`（google-generativeai / google.generativeai は使用しない）
- **認証**: AI Studio APIキー（環境変数 `GOOGLE_API_KEY`）、Vertex AI / サービスアカウントは不使用

#### 2.1.2 追加生成（20枚）
- **ミックス枠 10枚**: 2軸を混合したプロンプト（500–800 文字に抑える）
- **リラン枠 10枚**: 基本生成と同一条件をそのまま再実行し、seed 制御なしで分散を見る枠（seed は明示しない）

#### 2.1.3 Thinking 画像の扱い
- Gemini 3 Pro Image は途中の試行画像（thinking images）を返すことがある
- 複数の画像パートがある場合は「最後の画像パート」を最終画像として保存
- 画像パートが1つしかない場合はそれを最終画像とみなす（thinking が返らないケースを許容）
- オプションで thinking 画像も `{base}_thought_01.png` など別名で保存可

### 2.2 軸（Axis）システム
以下の10軸を使用する。

| 軸ID | 軸名 | 説明 |
|------|------|------|
| synesthesia | 共感覚 | 感覚を視覚へ変換 |
| biomimicry | 生体模倣 | 生物構造 → 人工物 |
| literal_interpretation | 直訳 | 慣用句/メタファーを物理化 |
| macro_micro | スケール崩壊 | 極小/巨大/断面 |
| material_paradox | 材質パラドックス | 状態・素材 × 物体 |
| glitch_contradiction | グリッチ/矛盾 | 相反指示 |
| affordance_inversion | 機能逆転 | 用途を反転 |
| representation_shift | 表現形式変換 | 図面/特許/回路/説明書化 |
| manufacturing_first | 制作制約 | 3Dプリント/木工などの制約優先 |
| procedural_rules | ルール生成 | 形状ではなく生成ルールを指定 |

### 2.3 束（Bundle）とドメイン
6束 × 各5ドメイン = 30ドメイン。各束内のドメインは 8 回の生成でラウンドロビン（または等重み）で均等に走査し、偏りを防ぐ（生成計画に domain_id を固定で記録）。

| 束ID | 束名 | ドメイン例 |
|------|------|-----------|
| bio_medical | 生体・医療・人間 | 手術室、病理、歯科、リハビリ、獣医 |
| food_scent_chem | 食・香り・化学プロセス | 発酵、分子料理、調香、染色、実験化学 |
| legal_finance | 法務・金融・制度 | 裁判、税務、保険、銀行、契約 |
| infra_industrial | 物流・インフラ・産業 | 港湾、鉄道、発電所、建設、廃棄物処理 |
| ritual_backstage | 儀礼・舞台裏・競技 | 宗教儀礼、葬儀、伝統工芸、スポーツ戦略、舞台裏 |
| human_ops | 人間系オペレーション | 学校、保育、介護、採用、コールセンター |

### 2.4 トレーサビリティ
#### 2.4.1 メタデータ記録
**基本情報**
- `run_id`, `index`, `created_at`
- `model` = `gemini-3-pro-image-preview`
- `image_resolution` = `2K`

**生成条件**
- `axis_id`, `bundle`, `domain_id`
- `template_text`, `final_prompt`
- `hints_used`, `vocab_used`
- `generation_type`（standard/mix/rerun）

**レスポンス情報**
- `image_part_index`, `total_image_parts`, `is_thought`
- `thought_images_saved`
- `response_metadata`: `finish_reason`, `safety_ratings`, `model_version`

**エラー情報**
- `error`, `error_type`, `http_status`, `retry_count`

#### 2.4.2 出力構造
```
./out/
  ├── {axis_id}/
  │   └── {bundle}/
  │       └── {domain_id}/
  │           ├── {timestamp}_{index}_{axis}_{bundle}_{domain}.png
  │           ├── {timestamp}_{index}_{axis}_{bundle}_{domain}.json
  │           └── {timestamp}_{index}_{axis}_{bundle}_{domain}_thought_01.png  # オプション
  └── manifest.jsonl
```

### 2.5 再開機能
- 初回に 500件の `plan.jsonl`（axis_id/bundle/domain_id/generation_type/source_index など計画全体）を保存し、再開時はそれを読み込む。
- `manifest.jsonl` を併用して、plan 上の該当 index をスキップして再開する。

---

## 3. 非機能要件
### 3.1 パフォーマンス
- 500枚の画像を安定して生成できること
- API制限を考慮した適切なレート制御

### 3.2 信頼性
- 失敗時は指数バックオフ（2秒→4秒→8秒）で最大3回リトライ
- リトライ失敗時はスキップして続行し、エラーを記録

### 3.3 可用性
- 途中停止からの再開機能
- 進捗表示（tqdm）

### 3.4 保守性
- Python 3.10+ 対応
- 依存は最小限（google-genai, pyyaml, tqdm, python-dotenv）

---

## 4. 制約条件
### 4.1 技術的制約
- SDK: `google-genai` に統一
- モデル: `gemini-3-pro-image-preview`
- 解像度: 2K固定（config.image_config で指定）
- 認証: AI Studio APIキー（環境変数 `GOOGLE_API_KEY` のみ）

### 4.2 生成ルール制約
- `hints` は毎回2個だけ使用
- `context` は必ずプロンプトに含める
- ミックス枠プロンプトは 500–800 文字程度に抑える
- Thinking画像と最終画像を混同しないよう、最終画像保存を保証する

---

## 5. 成功指標
### 5.1 定量指標
- 500枚生成成功率 95%以上
- メタデータ記録完全性 100%
- 最終画像の正確な保存率 100%

### 5.2 定性指標
- 生成画像から「当たり軸」「当たり束」を特定できる
- 任意の画像の生成条件を100%復元できる
- Thinking画像と最終画像を明確に区別できる

---

## 6. 用語定義

| 用語 | 定義 |
|------|------|
| 軸（Axis） | 入力を変換する生成ルール |
| 束（Bundle） | 性質が近いドメインのグループ |
| ドメイン（Domain） | 語彙・世界観の領域 |
| ヒント（Hints） | ドメインに紐づくキーワード（10語） |
| セレンディピティ | 予期しない発見や創造的偶然 |
| 当たり | ユーザーが良いと評価した画像 |
| Thinking画像 | 最終画像生成前の途中試行画像 |
| 最終画像 | レスポンスの最後の画像パート（1パートのみならそれを採用） |




