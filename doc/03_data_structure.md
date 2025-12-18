# Serendipity Mining - データ構造定義書

## 1. 概要
本システムで使用するデータ構造を定義する。主要なデータファイルは以下の3つ。
- `domains.yaml` - 30ドメイン定義
- `vocab.yaml` - 語彙辞書
- `axis_templates.yaml` - 10軸のプロンプトテンプレート

---

## 2. domains.yaml
### 2.1 スキーマ
```yaml
domains:
  - bundle: string          # 束ID（必須）
    domain_id: string       # ドメインID（一意）
    context: string         # 説明文（英語、簡潔）
    hints: [string]         # ヒント語リスト（10語）
```

### 2.2 束一覧
| 束ID | 説明 | ドメイン数 |
|------|------|-----------|
| bio_medical | 生体・医療・人間 | 5 |
| food_scent_chem | 食・香り・化学プロセス | 5 |
| legal_finance | 法務・金融・制度 | 5 |
| infra_industrial | 物流・インフラ・産業 | 5 |
| ritual_backstage | 儀礼・舞台裏・競技 | 5 |
| human_ops | 人間系オペレーション | 5 |

### 2.3 完全なドメイン定義
`domains.yaml` に30件を列挙する。例を抜粋:
```yaml
domains:
  - bundle: bio_medical
    domain_id: operating_room
    context: "Sterile operating room, surgical lighting, stainless steel surfaces, calm tension."
    hints: [sterile_drape, anesthesia_monitor, scalpel, suture, stainless_tray, surgical_mask, IV_pole, cautery_smoke, blue_gown, heart_rate_waveform]
  # ... 29 domains 続き
```

---

## 3. vocab.yaml
### 3.1 スキーマ
```yaml
vocab:
  CATEGORY_NAME:
    - word1
    - word2
```

### 3.2 語彙カテゴリ
| カテゴリ | 説明 | 使用軸 |
|---------|------|--------|
| OBJECT | 物体・プロダクト | material_paradox, biomimicry など |
| THING | モノ＋空間＋仕掛け | affordance_inversion |
| SUBJECT | シーン/対象 | synesthesia, macro_micro など |
| MATERIAL_OR_STATE | 素材・状態 | material_paradox |
| SENSATION | 感覚（味/匂い/音/触感など） | synesthesia |
| BIO_STRUCTURE | 生物構造 | biomimicry |
| IDIOM | 慣用句 | literal_interpretation |
| STYLE_A / STYLE_B | スタイル | glitch_contradiction |
| WRONG_FUNCTION | 逆転させる機能 | affordance_inversion |
| CONSTRAINT | 制作制約 | manufacturing_first |
| RULESET | 生成ルール | procedural_rules |

### 3.3 完全な語彙定義
`vocab.yaml` に各カテゴリの語を列挙する。

---

## 4. axis_templates.yaml
### 4.1 スキーマ
```yaml
axis_templates:
  axis_id:
    name: string           # 軸名（日本語）
    description: string    # 説明
    template: string       # プロンプトテンプレート
    placeholders:          # 使用するプレースホルダ
      - PLACEHOLDER_NAME
```

### 4.2 軸定義の例
```yaml
axis_templates:
  material_paradox:
    name: 材質パラドックス
    description: 状態・素材 × 物体
    template: "A product photo of '{OBJECT}' made entirely of '{MATERIAL_OR_STATE}'. {context} Subtle motifs: {h1}, {h2}. Highly detailed, realistic lighting."
    placeholders: [OBJECT, MATERIAL_OR_STATE]
  # ... 他9軸
```

---

## 5. 出力メタデータ（JSON）
### 5.1 フィールド一覧
| カテゴリ | フィールド | 型 | 説明 |
|---------|-----------|----|------|
| 基本情報 | run_id | string | 実行識別子（例: run_20240115_123456） |
|  | index | int | 0-499 の連番 |
|  | created_at | string | ISO8601 の生成日時 |
|  | model | string | `gemini-3-pro-image-preview` 固定 |
|  | image_resolution | string | `2K` 固定（config.image_config で指定） |
| 生成条件 | axis_id | string | 軸ID |
|  | bundle | string | 束ID |
|  | domain_id | string | ドメインID |
|  | template_text | string | プレースホルダ未展開のテンプレート |
|  | final_prompt | string | 最終プロンプト（展開済み） |
|  | hints_used | [string] | 使用したヒント2語 |
|  | vocab_used | object | プレースホルダに埋めた語彙 |
|  | generation_type | string | standard / mix / rerun |
| 画像情報 | image_part_index | int? | 保存した画像パートのインデックス |
|  | total_image_parts | int? | レスポンス中の画像パート総数 |
|  | is_thought | bool? | thinking画像か（最終画像は false） |
|  | thought_images_saved | [string] | 保存した thinking 画像のファイル名 |
| レスポンス | response_metadata | object? | `finish_reason`, `safety_ratings`, `model_version` |
| エラー | error | string? | エラーメッセージ |
|  | error_type | string? | SAFETY_BLOCKED / RATE_LIMITED / ... |
|  | http_status | int? | HTTPステータス（取得できる場合） |
|  | retry_count | int | リトライ回数 |

### 5.2 画像パート判定ルール
- 画像パートが複数ある場合は「最後の画像パート」を最終画像とする（thinking は最後以外）。
- 画像パートが1つしかない場合はそれを最終画像とする（thinking なしケースのガード）。
- `inline_data.data` が bytes ならそのまま保存、str なら base64 デコードして保存。

### 5.3 manifest.jsonl
- 1行1 JSON（上記フィールドをそのまま格納）を append で追記。

### 5.4 plan.jsonl（推奨）
- 500件の生成計画を保存する JSONL。フィールド例: `index, axis_id, bundle, domain_id, generation_type, source_index`。
- 再開時は plan.jsonl を読み、manifest.jsonl に存在する index をスキップする。

---

## 6. 生成タイプ
| タイプ | 説明 | 枚数 |
|--------|------|------|
| standard | 基本生成（軸×束×ドメイン） | 480 |
| mix | 2軸混合 | 10 |
| rerun | 同一条件を seed 指定なしで再実行（同一 final_prompt を使う） | 10 |

---

## 7. 軸×語彙マッピング
| 軸 | プレースホルダ → 語彙カテゴリ |
|----|------------------------------|
| synesthesia | SENSATION → SENSATION, SUBJECT → SUBJECT |
| biomimicry | OBJECT → OBJECT, BIO_STRUCTURE → BIO_STRUCTURE |
| literal_interpretation | IDIOM → IDIOM |
| macro_micro | SUBJECT → SUBJECT |
| material_paradox | OBJECT → OBJECT, MATERIAL_OR_STATE → MATERIAL_OR_STATE |
| glitch_contradiction | STYLE_A → STYLE_A, STYLE_B → STYLE_B, SUBJECT → SUBJECT |
| affordance_inversion | THING → THING, WRONG_FUNCTION → WRONG_FUNCTION |
| representation_shift | SUBJECT → SUBJECT |
| manufacturing_first | OBJECT → OBJECT, CONSTRAINT → CONSTRAINT |
| procedural_rules | RULESET → RULESET, SUBJECT → SUBJECT |
