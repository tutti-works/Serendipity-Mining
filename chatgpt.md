


意見としては、「カテゴリ（軸）」は“テーマ分け”というより、**生成を意図的に偏らせるための操作レバー（生成オペレータ）**として設計すると強いです。あなたの引用にある6軸は、その観点でかなり良い線いってます（人間の発想ルートを変える軸＝多様な失敗/成功パターンが出る）。

---

## 軸の決め方：おすすめの考え方（実務的）

### 1) 軸は「何を変えるか」で作る（テーマではなく変換）

良い軸＝**入力の変換規則が明確**で、生成結果の差が安定して出るもの。

* 例：スケール崩壊／材質パラドックス／慣用句直訳／生体模倣
  → どれも「変換の仕方」がはっきりしている

逆に弱い軸＝単なるジャンル（例：ファンタジー、SF）
→ 結局スタイル寄りに収束しやすく、セレンディピティが減りがち

### 2) 軸は「互いに直交」するほど良い

同じ効果を出す軸が多いと、1800枚が似た方向に寄ります。
直交性の目安は「**違う失敗の仕方**が起きるか」。

* 言語のバグ：意味解釈ミス
* グリッチ：表現崩壊
* 生体模倣：構造の置換
* 共感覚：抽象→視覚の翻訳
  → 失敗モードが分かれてるので強い

### 3) 軸は「後で整理できるタグ」になるべき

1800枚の価値は、生成よりも**後から見返して再利用できる構造**で決まります。
軸はそのままフォルダ/タグになります。

* `axis=synesthesia` みたいに一意にラベル付けできることが重要

---

## 「6軸」は十分か？ → “十分だが、穴がある”

あなたの6軸は「認知ルート」ベースで良い。ただ、セレンディピティの方向性として**2つ足りない系統**があると思います。

### 追加すると強い2〜4軸（方向性が被りにくい）

1. **機能逆転（Affordance Inversion）**

* 「本来の用途」と真逆の用途で設計されたモノ
* 例：椅子が“照明”として振る舞う、ドアが“楽器”として最適化されている

2. **表現形式変換（Representation Shift）**

* “写真”ではなく、設計・解析・制作の形式に落とす
* 例：爆発の「青写真」、孤独の「特許図面」、時間の「組立図」、感情の「回路図」

3. **制作プロセス制約（Manufacturing-First）**

* 3Dプリント/木工/CNCなど「作り方」から形を縛る
* 例：一体造形・サポート禁止・層が見える・木目方向必須…など

4. **ルール生成（Procedural Rule）**

* 形を説明せず、生成ルールだけ渡す（パラメトリック発想に寄る）
* 例：「3回対称、曲率は単調増加、穴は素数個、厚みはグラデーション」

この4つは、既存6軸の「感覚/構造/言語/スケール/物理/限界」と被りにくいです。

---

## 1800枚での“軸設計”のおすすめ（管理しやすく、カオスも出る）

### パターンA：10軸×150枚 + ミックス300枚（おすすめ）

* 既存6軸 + 上の4軸 = 10軸
* 各軸150枚なら、1軸あたり「傾向」が見えて、整理もしやすい
* ミックス300は“事故枠”（意外な当たりが出る）

### パターンB：探索→適応配分（当たり軸に予算を寄せる）

* 各軸まず50枚（計500）生成
* “当たり率（保存率）”が高い軸に残り1300を配分
* セレンディピティは「当たり軸を見つける」工程で最大化しやすい

---

## 軸を決める一番堅い方法（結論）

**「軸＝生成オペレータ」**として作り、

1. 直交する10個くらい用意
2. 少量試作で“当たり率”を測り
3. 残りを適応配分
   が、1800枚を資産にする上で最も合理的です。

---

必要なら、あなたの用途（プロダクト/CG/世界観/建築寄り など）に合わせて、**「軸10個の定義」＋「各軸のプロンプト雛形」＋「混ぜ方（事故りすぎない制約）」**まで一気に案出しします。



私の質問：セレンディピティのためには私の趣味（プロダクト/CG/世界観/建築寄り など）に寄ってないのもあった方がいいと思うが、どう思う？提案してくれた10軸で十分？あと「当たり軸を見つける」というのは500からわたしが気になったものをピックアップして軸を見つけるってこと？



結論としては、**趣味に寄ってない成分は入れた方がいい**です。セレンディピティは「探索空間を広げる（遠い所も見る）」で増えます。プロダクト/CG/世界観/建築だけに寄せると、当たりは増えても“既知の延長”に収束しやすいです。

## 「寄ってない成分」をどう入れるのが効率的か

軸（オペレータ）を増やすより、**軸はそのままに“ドメイン（語彙領域）”を増やす**のが一番効きます。

* **軸**＝発想の変換規則（スケール崩壊、直訳、表現形式変換…）
* **ドメイン**＝語彙の世界（医療、料理、金融、宗教儀礼、スポーツ戦術、法律、農業、教育、物流、軍事、恋愛、子育て…）

同じ「表現形式変換」でも、ドメインが違うと全く別物が出ます。

### 具体案（おすすめ）

* 10軸は維持しつつ、**ドメインを20〜30個用意**して、各生成でランダムに1つ選ぶ
* さらに「外れドメイン（あなたが普段触れない領域）」を意図的に混ぜる（例：保険、税、病理、港湾物流、宗教儀礼、スポーツ分析、裁判資料、農業、化学プラント）

これで「趣味に寄ってないのも混ぜる」を、管理可能な形で実現できます。

## 10軸で十分？

**十分です（初回としては最適レンジ）**。
理由は単純で、1800枚という規模だと「軸を増やすほど1軸あたりの枚数が減って傾向が読めない」「管理コストが増える」からです。

目安：

* 8〜12軸：傾向が掴めて、探索も回る（おすすめ）
* 15軸以上：1軸あたりが薄くなり、評価が難しくなりがち

ただし、10軸に“欠けているタイプ”があるなら増やす価値があります（例：**機能逆転**や**制作制約**は追加価値が大きい）。でもまずは10軸で回して、後で入れ替えで十分です。

## 「当たり軸を見つける」の意味（あなたの理解でほぼ合ってる）

あなたの言うとおりで、基本は：

1. まず500枚を「軸ごとに均等に」出す（例：10軸×30枚＝300 + ミックス200＝500）
2. あなたが**気になった画像をピックアップ（★付け）**する
3. その★が「どの軸から出たか」を集計して、**★率が高い軸＝当たり軸**と判断する
4. 残り1300枚を、当たり軸に多め配分して生成する

ここで重要なのは、「軸を新発見する」というより **“用意した候補軸の中で勝ち筋を見つける”**という意味です。

### もう一段だけ精度を上げるなら

* ★率だけでなく「上位10%の密度」「似た当たりの連発具合」も見る
* 当たり軸に寄せつつ、**最低でも各軸5〜10%は残して探索**する（探索枠ゼロにするとセレンディピティが死にます）

---

もしよければ、あなたの10軸を「軸（変換規則）」として固定しつつ、**ドメイン30個リスト**（うち“普段触れない領域”多め）をこちらで提案して、500枚の試作配分（10×30 + Mix200）まで具体化します。そうすると「寄ってないのも混ぜたい」が、運用の手間を増やさず実現できます。



私の質問：いまいちよくわかってないのだけど、○○×○○みたいなのを500枚生成するわけじゃないの？



はい、基本は **「○○×○○（＝単語Aと単語Bの掛け合わせ）」を大量に作って画像を生成する** で合っています。
ただし、私が言っていた「軸」は、その **○○ と ○○ の“作り方（掛け合わせのルール）”**を複数用意しよう、という話です。

---

## 「500枚生成」の中身はこうなる

500枚＝**500個のプロンプト**を作って、画像を500枚生成する。
そのプロンプトは、基本的に毎回こういう形：

* **Aリストから1語**選ぶ
* **Bリストから1語**選ぶ
* それをテンプレに差し込む

つまり **500回、○○×○○を引く**イメージです。

---

## 「軸」って何を変えるの？

軸＝「○○×○○」の **○○の種類**と **テンプレ（指示文）** を変えることです。

例：

### 軸：材質パラドックス

* ○○（素材/状態） × ○○（物体）
* 例：`溶岩` × `ソフトクリーム`
* テンプレ：`A product photo of a [Object] made of [Material/State] ...`

### 軸：共感覚

* ○○（味/匂い/音/触感） × ○○（物体/風景）
* 例：`チェロの重低音` × `高層ビル群`
* テンプレ：`A scene that looks like [Sensation], depicted as [Object/Scene] ...`

### 軸：生体模倣

* ○○（生物構造） × ○○（工業製品）
* 例：`甲虫の殻` × `ゲーミングマウス`

### 軸：機能逆転

* ○○（用途） × ○○（本来違う物体）
* 例：`椅子として機能する` × `街灯`

こういう “○○と○○の定義” を変えるのが軸です。

---

## じゃあ「10軸×試作500枚」はどう配るの？

例として、こういう設計にすると分かりやすいです：

* **10軸 × 30枚 = 300枚**（各軸の「○○×○○」を30回引く）
* **Mix 200枚**（軸を2つ以上混ぜて “○○×○○×○○” にする事故枠）

ここでいう「30枚」は、

* その軸のルールに従って **30回ランダムに○○×○○を生成して、30枚作る**
  という意味です。

---

## 「○○×○○」だけじゃないケースもある（でも発想は同じ）

一部の軸は、掛け合わせが「×」じゃなくなることがあります。

* 慣用句直訳：`Idioms（1個）` をそのまま入れる（×が不要）
* グリッチ：`矛盾指示（1個〜複数）` を積む（×より“制約の束”）

ただ、運用としては「入力の部品を組み合わせてプロンプトを作る」という点で同じです。

---

## まとめ（あなたの疑問への答え）

* **はい、○○×○○みたいなのを（ランダムに）500回作って、500枚生成する**のが基本です。
* 「軸」は、その○○×○○の **部品の種類**（素材×物体、感覚×風景…）と **テンプレ**を変えて、出る絵の種類を意図的に散らすための設計です。

もしよければ、あなたの目的に合わせて「10軸」を確定して、各軸ごとに
**Aリスト例20語＋Bリスト例20語＋テンプレ1本**をこちらで具体化します。そうすると「500枚」が一気に現実的になります。



私の質問：「ドメイン30個リスト」というのは軸：材質パラドックスでいうところの（素材/状態）が30単語、（物体）が30単語でランダムな組み合わせで30枚生成ということ？



違います。私が言った「ドメイン30個」は、**単語リスト（素材30語・物体30語）そのもの**ではなく、もっと上位の **“語彙の世界／文脈の領域”** です。

### まず定義を分けると整理しやすい

* **軸**：掛け合わせのルール（例：材質パラドックス＝「素材/状態 × 物体」）
* **ドメイン**：その掛け合わせをどの世界の語彙でやるか（例：医療、料理、港湾物流、保険、宗教儀礼…）

---

## ドメイン30個を使うと、何が起きる？

### 使い方A（おすすめ）：ドメインごとに“小さな語彙プール”を持つ

「材質パラドックス」軸は同じでも、ドメインで **素材/状態 と 物体の候補が変わる**ようにします。

例：軸＝材質パラドックス

* ドメイン：**医療**

  * 素材/状態候補：滅菌パック、ゲル、ラテックス、消毒液、X線フィルム…
  * 物体候補：聴診器、点滴スタンド、車椅子、手術灯…
* ドメイン：**料理**

  * 素材/状態候補：出汁、泡、ゼラチン、飴細工、焦げ…
  * 物体候補：包丁、まな板、冷蔵庫、フライパン…
* ドメイン：**港湾物流**

  * 素材/状態候補：防錆塗装、オイル、コンテナシール、パレット材…
  * 物体候補：コンテナ、クレーン、フォークリフト、通関書類…

この場合、
「ドメイン30個」＝ **“30個の語彙セットの束”** という意味になります。
（単語30個という意味ではありません）

### 使い方B（軽量）：単語プールは共通のまま、ドメインを“背景文脈”として足す

素材リストと物体リストは共通にして、プロンプトに一行だけ入れます。

例：

* `A product photo of a [Object] made of [Material]. Context: in a hospital sterilization room.`
* `Context: inside a cargo terminal inspection area.`

これは運用が簡単で、後から「医療っぽい当たり」みたいな分析がしやすいです。

---

## あなたの質問にそのまま答えると

> 「軸：材質パラドックスでいうところの（素材/状態）が30単語、（物体）が30単語でランダムな組み合わせで30枚生成？」

* それは **“ドメイン30個”の意味ではない**です。
* それは単に「素材30語×物体30語」の設計で、ドメインとは別のレイヤーです。

---

## 実務的なおすすめ（500枚試作に向く形）

* まず「軸」を選ぶ（例：材質パラドックス）
* 次に「ドメイン」をランダムに選ぶ（例：医療）
* そのドメインの語彙プールから「素材/状態」「物体」を引いて、1枚生成

こうすると「趣味外ドメイン」を混ぜても破綻しにくく、しかも後でタグで整理できます。

必要なら、ドメイン30個を「あなたが普段触れない領域多め」で作って、各ドメインにつき **素材候補20・物体候補20** みたいな“最小語彙プール”まで具体化します。



私の質問：素材候補や物体候補はそれぞれのドメインごとに20で十分なの？また、パターンA：10軸×150枚 + ミックス300枚と比べてメリットデメリットを教えて



## 1) ドメインごと「素材20・物体20」で十分？

**“十分になる条件”次第**です。結論から言うと、**試作〜中規模（数百〜千枚）なら20でまず足ります**。ただし「同一ドメインに寄せて大量に出す」場合は足りなくなります。

### なぜ20でも回るのか（組み合わせ数の観点）

* 1ドメイン内で `素材20 × 物体20 = 400通り` の組み合わせが作れます。
* 例えば「10軸×150枚（=1500枚）」を **30ドメインで散らす**なら、総セル数は `10軸×30ドメイン=300セル`。平均すると **1セルあたり5枚**程度しか生成しません。
  → この密度なら、素材20・物体20でも枯渇しません。

### 20が足りなくなりやすいケース

* 当たりドメインが見つかって **同じドメインで300枚〜600枚**回し始める
  （400通りに近づくと重複が増え、既視感が出やすい）
* “素材”側が抽象的で似た意味が多い（gel / slime / goo みたいに収束）
* “物体”側がドメイン固有で種類が少ない（医療器具だけ等）

### 実務のおすすめ

* 最初は **20/20でOK（作るのが速い）**
* 当たりドメインだけ **50/50に増やす**（投資は勝ち筋に集中）
* さらに「同義語の増量」より **“サブカテゴリ分割”**が効きます
  例：医療→「器具」「薬剤」「手術室」「検査」「衛生」などに分け、それぞれ20ずつ持つ

---

## 2) 「ドメイン導入」方式 vs パターンA（10軸×150 + ミックス300）の比較

### パターンA：10軸×150枚 + ミックス300枚

**メリット**

* 設計が単純で、運用が楽（軸だけ管理すればよい）
* 1軸150枚あるので、軸ごとの“絵の癖”が掴みやすい
* 当たり軸の判定がしやすい（タグが軸だけなので分析が簡単）

**デメリット**

* 語彙があなたの得意領域（プロダクト/CG/建築）に寄っていると、**結果も寄りやすい**
  → “想定内の良い絵”は増えるが、“異物混入”が減る
* ミックス300は事故が出る一方、**事故の原因分析が難しい**（何が効いた事故なのか）

### ドメイン導入（軸は同じ、語彙世界を30領域に散らす）

**メリット**

* セレンディピティが上がりやすい（遠い語彙が混ざる＝発想空間が広がる）
* 「趣味外」要素を、破綻しにくい形で投入できる（背景文脈としても、語彙としても）
* 後で「当たりは“軸×ドメイン”のどこか」が分かる
  → 例：材質パラドックスは強いが、港湾物流ドメインのとき特に当たり、など

**デメリット**

* 設計コストが増える（ドメイン定義・語彙プール作成）
* 品質ブレが増える（ドメインによって“絵が散る”ので、駄作も増える）
* 分析が二次元になる（軸だけでなくドメインも見る必要）

---

## どっちが良い？（おすすめは“ハイブリッド”）

あなたの目的が「セレンディピティ最大化」なら、**パターンA単体より、Aにドメインを軽く混ぜる**のがバランス良いです。

### ハイブリッド案（運用が簡単で効果が出る）

* 基本は **パターンA（10軸×150 + ミックス300）**のまま
* ただし各プロンプトに **ドメインタグ（文脈1行）**をランダム付与する

  * 語彙プールは共通でOK（最初はB方式：背景文脈だけ）
  * 当たりが出たドメインだけ、A方式（ドメイン専用語彙20/20）に深化

これなら「管理のしやすさ（Aの強み）」を保ちつつ、「趣味外混入（ドメインの強み）」を獲得できます。

---

## まとめ

* **ドメインごと20/20は“最初は十分”**。当たりドメインだけ増やすのが合理的。
* **パターンAは運用と分析が簡単**、ただし発想が寄りやすい。
* **ドメイン導入はセレンディピティに強い**が、設計と分析が重くなる。
* おすすめは **Aをベースにドメインを軽く混ぜ、当たりだけ深化**。

必要なら、あなたの「趣味外成分」を狙って、**ドメイン30（うち20は普段触れない領域）**をこちらで具体案として出し、さらに「最初は背景文脈で混ぜる版」「語彙20/20まで作る版」の2段階で提案します。



私の質問：でも試作500枚ってことは各ドメインごとに1枚だけ生成ってことだよね？一枚で当たりかどうかを判断するのは早計じゃない？



その懸念は正しいです。**「ドメイン30個を用意したから、試作500枚＝各ドメイン1枚」**みたいに設計すると、判断はほぼ運ゲーになります。
試作の目的は「当たりを当てる」ではなく、**当たりやすい条件の“傾向”を推定する**ことなので、最低限のサンプル数が要ります。

---

## まず整理：500枚試作＝「各ドメイン1枚」ではない

500枚の配り方は自由です。重要なのは、

* **1枚で判断しない**
* でも**全ドメインを均等に厚くはできない**（500だと薄まる）

なので、現実的には **ドメインを一旦“絞って”試す**か、**ドメインを束ねて試す**のが合理的です。

---

## どれくらいの枚数があれば「当たりかどうか」を判断できる？

目安として、**1ドメインあたり最低でも5〜10枚**は欲しいです。

* n=1：当たり率の推定が不可能（偶然に全部左右される）
* n=5：まだ粗いが「死んでる／可能性ある」の一次判定はできる
* n=10：当たり率の差が見え始める（“当たりやすい”を選別できる）

---

## じゃあ500枚試作をどう配ればいい？（おすすめ3パターン）

### パターン1：ドメインを絞って厚く（おすすめ）

* ドメインを最初から30全部使わず、**12ドメイン程度に絞る**
* 例：**10軸 × 12ドメイン × 3枚 = 360枚**
  残り140枚はミックス／変種（同一条件での別seed）に回す
* メリット：各ドメインが最低3枚確保され、比較が成立しやすい
* デメリット：未採用のドメインは“この500枚では評価できない”

### パターン2：ドメイン30は維持しつつ「束」で評価（管理が楽）

* 30ドメインを、性質が近いもので**6グループ（各5ドメイン）**に束ねる
  例：医療・化学・法務・物流・宗教儀礼・スポーツ、みたいな束
* 500枚の中では「束」単位で回す（束内からドメインをランダム選択）
* メリット：30を捨てずに比較可能／デメリット：束内の差は後段でしか見えない

### パターン3：ドメインは“背景文脈タグ”として軽く混ぜる（薄くても効く）

* 最初は語彙プールを共通にして、プロンプトに
  `Context: ...` を足すだけ（ドメイン差を弱めに入れる）
* これなら「1ドメイン1枚」でも多少は傾向が見えるが、確度は下がる

---

## 「当たり軸を見つける」はどうやるのが正しい？

あなたの理解（ピックアップして軸を見つける）で方向は合ってますが、運用としてはこうです：

1. 500枚を見て、**各画像を★0/1（または0/1/2）で評価**
2. 画像には必ず **(軸, ドメイン, seed, 使った語彙)** をメタデータで持たせる
3. 集計して

   * ★率が高い **軸**
   * ★率が高い **ドメイン（またはドメイン束）**
   * ★率が高い **軸×ドメインの組**
     を見つける
4. 次の1300枚は、その“勝ち筋”に寄せつつ、探索枠を残す

ポイントは「軸を新発見する」ではなく、**用意した条件のどこが勝ち筋かを統計的に見つける**ことです。

---

## 実務的なおすすめ（迷いを減らす結論）

* 500枚で「30ドメイン全部を公平に評価」は無理がある
* だから **(A) 最初は12ドメインに絞って厚く試す**か、**(B) 30を束ねて試す**のが堅い
* その後、当たり束（or当たりドメイン）だけ語彙を増やす（20/20→50/50）

---

もしあなたが「趣味外を混ぜたい」意図を強く持っているなら、私の推しは **パターン2（束）**です。
次の返答で、あなた向けに「30ドメイン案」を **“6束×5ドメイン”**に整理して、500枚の具体配分（軸×束×枚数）まで落として提示できます。



私の質問：パターン2（束）で提示して



了解。**パターン2（束＝ドメイン束）**として、「30ドメインを6束×5ドメイン」に整理し、**試作500枚の配分**まで落とします。

---

## 6束×5ドメイン（＝30ドメイン案）

「趣味（プロダクト/CG/建築）から遠い語彙」を意図的に混ぜる設計です。

### 束1：生体・医療・人体

* 手術室/医療機器
* 病理・顕微鏡世界
* 歯科・矯正
* リハビリ・義肢装具
* 獣医・動物病院

### 束2：食・香り・化学プロセス

* 発酵/醸造
* 分子料理・泡/ゲル
* 調香・香料
* 染色・顔料・インク
* 実験化学・ラボ器具

### 束3：法務・金融・制度（書類の世界）

* 裁判・法廷手続き
* 税務・申告
* 保険査定
* 銀行与信・審査
* 契約・特許・規格

### 束4：物流・インフラ・産業オペレーション

* 港湾物流・コンテナ
* 鉄道運行・信号
* 発電所・配電盤
* 建設現場・重機
* 廃棄物処理・リサイクルプラント

### 束5：儀礼・舞台裏・競技

* 宗教儀礼・典礼
* 葬儀・弔いの道具立て
* 伝統工芸（所作・段取り）
* スポーツ戦術・アナリティクス
* 舞台裏（照明・音響・転換）

### 束6：人間系オペレーション（現場の摩擦）

* 学校運営・評価・試験
* 保育・子育て現場
* 介護・ケア現場
* 採用面接・人事
* コールセンター・顧客対応

---

## 試作500枚の配分（“束”で評価できるようにする）

「1ドメイン1枚」にならないよう、**束×軸**で最低限のサンプル密度を確保します。

### 配分案（おすすめ）

* **480枚：10軸 × 6束 × 8枚**

  * 各“軸×束”セルに8枚あるので、偶然のブレが多少なら平均化できます。
* **20枚：ミックス枠**（後述）

> これで、各束は **10軸×8枚＝80枚**、各軸は **6束×8枚＝48枚** 持つので、束・軸どちらも比較が成立します。

---

## 10軸（固定）をどう使うか

軸は「○○×○○の作り方（変換規則）」です。例として10軸はこう置けます：

1. 共感覚（感覚→視覚）
2. 生体模倣（生物構造→人工物）
3. 直訳（慣用句/メタファーの物理化）
4. スケール崩壊（極小/巨大/断面）
5. 材質パラドックス（状態/素材×物体）
6. グリッチ/矛盾（相反指示）
7. 機能逆転（用途の反転）
8. 表現形式変換（図面/特許/回路/説明書化）
9. 制作制約（3Dプリント/木工など制約先行）
10. ルール生成（形ではなく生成ルールで縛る）

---

## 「束」をプロンプトに入れる方法（運用が軽い順）

束（ドメイン束）は、単語リストを大量に作らなくても効かせられます。

### 方法A（軽量・おすすめ）：共通の○○×○○に「文脈タグ」を足す

* 例（材質パラドックス）
  `A product photo of a [Object] made of [Material/State]. Context: [Domain]. Include hints: [k1], [k2].`
* 各ドメインは「Context文（1行）」＋「ヒント語10個」だけあれば開始できます。

### 方法B（重いが強い）：ドメインごとにA/B語彙プールを持つ

* ドメインごとに「素材/状態」「物体」を各20ずつ…みたいな形。
* 本番（当たり束が見えた後）に寄せるのが効率的です。

---

## 20枚のミックス枠（おすすめの使い方）

* **10枚：フルミックス事故枠**（軸を2〜3個混ぜる）
* **10枚：リシード枠**（試作480から「良かったセル（軸×束）」を選び、同条件でseedだけ変えて10枚）

---

## 500枚から「当たり束/当たり軸」を見つける手順（誤判定を減らす）

あなたがやるのは「選ぶ」だけでOKです。

1. 画像に★（0/1 or 0/1/2）を付ける
2. 画像メタデータとして **軸ID・束ID・ドメイン名・プロンプト** を保存しておく
3. 集計して、★率が高い順に

* 当たり**束**（どの語彙世界が刺さるか）
* 当たり**軸**（どの変換が刺さるか）
* 当たり**軸×束**（勝ち筋の組）
  を決める

---

## ここまでの結論

* 「束」でやるなら、**500枚でも評価は可能**（ただし配分設計が重要）
* 私の提示は「10軸×6束×8枚＝480」で、**“1枚で判断”問題を回避**しています
* ドメイン単語を20/20作り込むのは、**当たり束が見えてからで十分**です

必要なら次に、上の30ドメインそれぞれに対して「Context文（1行）」と「ヒント語10個」をこちらで具体的に埋めた“即運用できる雛形”まで出します。



私の質問：“即運用できる雛形”を出して



以下は、そのままJSON/YAMLとして使える **“即運用できる雛形”** です。
意図は「10軸は固定」しつつ、各生成ごとに **束→ドメイン→(ヒント語を2〜3個抽選)** を足して、趣味外の文脈を安定注入することです。

---

## 使い方（最短）

1. 生成ごとに `axis_id` を選ぶ（例：material_paradox）
2. `domain_id` を選ぶ（例：port_container_terminal）
3. そのドメインの `hints` から 2〜3語だけランダム抽選
4. 軸テンプレに差し込んで生成

   * **ポイント**：hints は全部入れない（情報過多で破綻しやすい）

---

## ドメイン30（6束×5）：「Context 1行」＋「Hints 10語」

```yaml
domains:
  # ===== Bundle 1: Bio / Medical / Human =====
  - bundle: bio_medical
    domain_id: operating_room
    context: "Sterile operating room, surgical lighting, stainless steel surfaces, calm tension."
    hints: [sterile_drape, anesthesia_monitor, scalpel, suture, stainless_tray, surgical_mask, IV_pole, cautery_smoke, blue_gown, heart_rate_waveform]

  - bundle: bio_medical
    domain_id: pathology_microscopy
    context: "Microscopy lab view, stained tissue slices, glass slides, clinical precision."
    hints: [histology_slide, hematoxylin, eosin_stain, petri_dish, microscope_objective, cell_nuclei, grid_reticle, lab_label, sample_vial, biohazard_symbol]

  - bundle: bio_medical
    domain_id: dental_orthodontics
    context: "Dental lab bench, molds and aligners, bright clinic lights, clean plastic textures."
    hints: [dental_mold, braces_wire, aligner_tray, enamel_gloss, xray_bitewing, suction_tube, orthodontic_chain, occlusion_mark, mouth_mirror, fluoride_gel]

  - bundle: bio_medical
    domain_id: rehab_prosthetics
    context: "Rehabilitation studio, prosthetics fitting, measured movement, human-centered engineering."
    hints: [carbon_fiber_laminate, gait_training, socket_fit, silicone_liner, actuator_joint, velcro_strap, force_plate, alignment_jig, foam_roller, physiotherapy_bands]

  - bundle: bio_medical
    domain_id: veterinary_clinic
    context: "Veterinary exam room, friendly but clinical, animal-scale equipment and care."
    hints: [exam_table, microchip_scanner, cone_collar, paw_print, ultrasound_gel, stethoscope, pet_carrier, vaccination_syringe, fur_clipping, treat_jar]

  # ===== Bundle 2: Food / Scent / Chemical Process =====
  - bundle: food_scent_chem
    domain_id: fermentation_brewery
    context: "Fermentation space, bubbling tanks, warm yeast aromas, industrial pipes and gauges."
    hints: [airlock_bubble, yeast_foam, wort, oak_barrel, hydrometer, fermentation_tank, sanitizer_spray, valve_handle, CO2_hose, temperature_gauge]

  - bundle: food_scent_chem
    domain_id: molecular_gastronomy
    context: "Experimental kitchen, foams and gels, precision plating, scientific cooking tools."
    hints: [spherification, agar_gel, siphon_foam, pipette_dropper, liquid_nitrogen_mist, micro_scale, plating_tweezers, glossy_reduction, edible_film, vacuum_bag]

  - bundle: food_scent_chem
    domain_id: perfumery
    context: "Perfumery studio, scent strips and amber bottles, delicate glass and labels."
    hints: [blotter_strip, amber_bottle, atomizer, top_note, base_note, accord, tincture_drop, maceration_jar, perfumer_palette, handwritten_formula]

  - bundle: food_scent_chem
    domain_id: dyes_pigments_ink
    context: "Pigment workshop, powders and stains, color swatches, messy controlled experimentation."
    hints: [pigment_powder, ink_bottle, color_swatches, staining_gloves, mortar_pestle, dye_bath, binder_medium, paint_muller, paper_bleed, chromatography_strip]

  - bundle: food_scent_chem
    domain_id: chemistry_glassware
    context: "Chem lab bench, glassware and fumes, safety markings, precise measurements."
    hints: [beaker, erlenmeyer, burette, fume_hood, hazard_pictogram, latex_glove, condenser_coil, pH_strip, reagent_label, stirring_bar]

  # ===== Bundle 3: Legal / Finance / Institutional =====
  - bundle: legal_finance
    domain_id: courtroom_procedure
    context: "Courtroom setting, formal procedure, records and evidence, quiet authority."
    hints: [gavel, witness_stand, evidence_bag, docket_number, transcript_page, seal_stamp, judge_robes, exhibit_label, bench_nameplate, oath_bible]

  - bundle: legal_finance
    domain_id: tax_filing
    context: "Tax paperwork flow, forms and checklists, stamps and receipts, bureaucratic calm."
    hints: [form_1040_like, receipt_stack, withholding, ledger_lines, red_stamp, checklist_boxes, envelope_window, barcode_label, calculator_tape, deadline_notice]

  - bundle: legal_finance
    domain_id: insurance_claims
    context: "Insurance assessment, documentation photos, damage reports, measured skepticism."
    hints: [claim_form, adjuster_clipboard, damage_photos, policy_number, estimate_sheet, watermark_copy, incident_timeline, appraisal_stamp, call_log, denial_reason_code]

  - bundle: legal_finance
    domain_id: bank_credit_underwriting
    context: "Credit review desk, risk scoring, statements and ratios, restrained seriousness."
    hints: [credit_score, cashflow_chart, covenants, risk_rating, collateral_photo, KYC_check, income_statement, debt_ratio, approval_signature, compliance_flag]

  - bundle: legal_finance
    domain_id: contracts_patents_standards
    context: "Contract/patent drafting, diagrams and clauses, standards language, precise definitions."
    hints: [clause_numbering, patent_figures, claim_1, definitions_section, ISO_reference, revision_mark, appendix_table, signature_block, confidentiality, version_control]

  # ===== Bundle 4: Logistics / Infrastructure / Industrial Ops =====
  - bundle: infra_industrial
    domain_id: port_container_terminal
    context: "Port container terminal, cranes and stacked containers, salty air, logistics rhythm."
    hints: [gantry_crane, container_stack, twist_lock, bill_of_lading, customs_seal, hazard_container, forklift, yard_map, ship_horn, reflective_vest]

  - bundle: infra_industrial
    domain_id: railway_signaling
    context: "Rail operations, signaling panels, timetables, safety-first systems engineering."
    hints: [signal_light, track_switch, control_panel, timetable_board, interlocking, relay_cabinet, platform_edge, overhead_lines, maintenance_tag, route_indicator]

  - bundle: infra_industrial
    domain_id: power_substation
    context: "Electrical substation, switchgear and warning signs, humming energy, strict geometry."
    hints: [switchgear, transformer, insulator_stack, caution_high_voltage, busbar, breaker_handle, grounding_rod, SCADA_screen, arc_flash_label, cable_trench]

  - bundle: infra_industrial
    domain_id: construction_heavy_machinery
    context: "Construction site, heavy machinery, dust and markings, loud organized chaos."
    hints: [excavator_arm, rebar_grid, concrete_formwork, safety_cone, survey_marks, hard_hat, crane_hook, scaffolding, caution_tape, site_plan]

  - bundle: infra_industrial
    domain_id: waste_recycling_plant
    context: "Recycling plant, sorting conveyors, compressed bales, industrial grit and order."
    hints: [conveyor_belt, sorting_chute, crushed_bale, residue_dust, shredder_teeth, barcode_bin, PPE_goggles, compactor, odor_mask, hazard_sign]

  # ===== Bundle 5: Ritual / Backstage / Competition =====
  - bundle: ritual_backstage
    domain_id: religious_liturgy
    context: "Ritual ceremony, symbolic objects, patterned textiles, reverent lighting."
    hints: [incense_smoke, altar_cloth, chant_book, ceremonial_bell, candle_row, sacred_symbol, procession, offering_bowl, gilded_detail, icon_frame]

  - bundle: ritual_backstage
    domain_id: funeral_mourning
    context: "Mourning setting, quiet flowers and fabrics, restrained color, solemn care."
    hints: [white_chrysanthemum, condolence_envelope, memorial_photo, black_ribbon, incense_stick, altar_table, soft_lantern, prayer_beads, folded_cloth, silence_space]

  - bundle: ritual_backstage
    domain_id: traditional_craft_workshop
    context: "Traditional craft studio, hand tools and jigs, material respect, slow precision."
    hints: [wood_shavings, hand_plane, marking_gauge, chisel_set, lacquer_gloss, joinery, workbench_vise, paper_pattern, sharpening_stone, apprentice_notes]

  - bundle: ritual_backstage
    domain_id: sports_strategy_analytics
    context: "Strategy room, play diagrams and metrics, competitive focus, data overlays."
    hints: [heatmap_overlay, playbook_diagram, coach_marker, possession_chart, formation_grid, stopwatch, headset_comms, scouting_report, win_probability, video_review]

  - bundle: ritual_backstage
    domain_id: theater_backstage
    context: "Theater backstage, rigging and cues, prop tables, controlled darkness."
    hints: [stage_rigging, cue_sheet, gaffer_tape, prop_table, spotlight_beam, curtain_rope, backstage_pass, makeup_mirror_bulbs, set_flat, scene_change]

  # ===== Bundle 6: Human Ops / Friction =====
  - bundle: human_ops
    domain_id: school_exam_admin
    context: "Exam administration, desks and sheets, strict rules, quiet pressure."
    hints: [answer_sheet, proctor_clock, seat_number, pencil_eraser, sealed_envelope, scoring_rubric, silence_sign, barcode_exam, attendance_check, instruction_page]

  - bundle: human_ops
    domain_id: childcare_nursery
    context: "Nursery classroom, small furniture, playful order, safety-oriented design."
    hints: [toy_bins, finger_paint, tiny_chairs, nap_mats, name_tags, picture_schedule, soft_blocks, snack_time, hand_sanitizer, story_corner]

  - bundle: human_ops
    domain_id: elder_care_facility
    context: "Care facility, gentle routines, assistive devices, calm supportive atmosphere."
    hints: [walker_frame, handrail, medication_tray, care_plan_sheet, meal_cart, nurse_call_button, compression_socks, mobility_aid, therapy_putty, quiet_tv]

  - bundle: human_ops
    domain_id: hiring_interview_hr
    context: "Interview setting, evaluation forms, polite tension, structured conversation."
    hints: [resume_packet, scorecard, competency_matrix, handshake, calendar_invite, panel_notes, salary_band, onboarding_checklist, background_check, decision_meeting]

  - bundle: human_ops
    domain_id: call_center_support
    context: "Customer support floor, scripts and dashboards, empathy under time pressure."
    hints: [headset, call_queue, escalation_tag, script_prompt, SLA_timer, ticket_id, hold_music, knowledge_base, angry_customer_note, resolution_code]
```

---

## 10軸の「テンプレ」雛形（そのままプロンプトに）

各プロンプトは **英語**推奨（生成モデルが安定しやすい）。`{context}` と `{h1}{h2}{h3}` に上のドメイン情報を差し込みます。

```text
[AXIS: synesthesia]
"Visualize the sensation of '{SENSATION}' as a tangible scene featuring '{SUBJECT}'. {context} Subtle motifs: {h1}, {h2}. Cinematic, high detail."

[AXIS: biomimicry]
"A product design of '{OBJECT}' inspired by the biological structure of '{BIO_STRUCTURE}'. {context} Subtle motifs: {h1}, {h2}. Studio lighting, crisp materials."

[AXIS: literal_interpretation]
"Depict the idiom '{IDIOM}' literally, as a coherent scene. {context} Subtle motifs: {h1}, {h2}. Surreal but readable."

[AXIS: macro_micro]
"An extreme-scale view of '{SUBJECT}' (macro/micro/cross-section). {context} Subtle motifs: {h1}, {h2}. Scientific yet artistic."

[AXIS: material_paradox]
"A product photo of '{OBJECT}' made entirely of '{MATERIAL_OR_STATE}'. {context} Subtle motifs: {h1}, {h2}. Highly detailed, realistic lighting."

[AXIS: glitch_contradiction]
"Create an image that is both '{STYLE_A}' and '{STYLE_B}' simultaneously, depicting '{SUBJECT}'. {context} Subtle motifs: {h1}, {h2}. Intentional contradictions."

[AXIS: affordance_inversion]
"Design '{THING}' that functions as '{WRONG_FUNCTION}' (unexpected use). {context} Subtle motifs: {h1}, {h2}. Plausible engineering."

[AXIS: representation_shift]
"A technical blueprint/patent diagram/operational manual page for '{SUBJECT}'. {context} Include labels and callouts. Motifs: {h1}, {h2}."

[AXIS: manufacturing_first]
"A manufacturable design of '{OBJECT}' constrained by '{CONSTRAINT}'. {context} Motifs: {h1}, {h2}. Looks buildable."

[AXIS: procedural_rules]
"Generate a form following rules: '{RULESET}'. Subject: '{SUBJECT}'. {context} Motifs: {h1}, {h2}. Clean composition."
```

---

## 最低限の“共通語彙”スターター（すぐ回すための短い種）

すでにあなたが単語リストを持っているなら不要。無い場合はこれで回せます。

* `OBJECT`（例）：chair, lamp, sneaker, teapot, drone, headset, kiosk, backpack, helmet, keyboard, bicycle, camera
* `MATERIAL_OR_STATE`（例）：molten_glass, aerogel, bioluminescent_fungus, smoke, mercury, obsidian, jelly, paper_origami, rust, ice
* `SUBJECT`（例）：library, bridge, city_block, bonsai, smartphone, altar, control_room, contract_page
* `SENSATION`（例）：low_cello, mint_coolness, burnt_sugar_smell, static_noise, velvet_touch, absolute_silence
* `BIO_STRUCTURE`（例）：beetle_shell, coral_branching, leaf_veins, fish_skeleton, honeycomb, mycelium
* `IDIOM`（例）：time_flies, raining_cats_and_dogs, skeleton_in_the_closet, walking_on_eggshells
* `STYLE_A/B`（例）：ultra_minimal, baroque, corporate_manual, kids_storybook, clinical_diagram, gothic
* `WRONG_FUNCTION`（例）：measures_heart_rate, filters_air, stores_evidence, performs_tax_audit, routes_cargo
* `CONSTRAINT`（例）：single_piece_print, no_supports, 2_axis_CNC_only, bent_sheet_metal_only, snap_fit_only
* `RULESET`（例）：prime_number_holes, 3_fold_symmetry, curvature_monotone, thickness_gradient, labels_every_10mm

---

## 運用のコツ（破綻しにくくする）

* `hints` は **毎回2個だけ**（多いと支離滅裂になりやすい）
* “趣味外”を強く出したいときは

  * `Context` を強める（例：Courtroom / Substation）
  * それでも崩れるなら `representation_shift`（図面化）軸が安定

---

必要なら次に、あなたの「10軸×6束×8枚＝480」試作のために、**各軸で使う語彙（OBJECT/MATERIAL…）をもう少しだけ拡張した“現場用ミニ辞書”**も、同じ形式で出します。



私の質問：“現場用ミニ辞書”も出して。'{THING}'の単語リストがないけどいいの？



出します。結論から言うと **`{THING}` の単語リストが無くても回せます**（`{THING}`＝`{OBJECT}` を代入すれば成立）。ただ **「機能逆転（affordance_inversion）」軸の当たり率**を上げるなら、`{THING}`は「モノ」だけでなく「空間・設備・書類・仕組み」も混ぜた専用リストがある方が強いです。

---

## “現場用ミニ辞書”（コピペ用 / snake_case）

* まずは各カテゴリ **30語前後**。生成前に増やすなら「当たり軸/束」だけ増量が効率的です。
* 使い方：毎回 `hints` は2個、各プレースホルダは1つ抽選。

```yaml
vocab:
  # ===== Core nouns =====
  OBJECT:  # 物体（プロダクト寄り）
    - chair - desk_lamp - sneaker - teapot - drone - headphones - keyboard - mouse
    - camera - backpack - wristwatch - helmet - bicycle - toaster - coffee_maker
    - microphone - router - game_controller - power_bank - water_bottle - umbrella
    - suitcase - flashlight - door_handle - thermostat - air_purifier - speaker
    - smart_display - electric_kettle - rolling_cart - safety_goggles

  THING:  # 「機能逆転」で使う主語（モノ＋空間＋仕組みも混ぜる）
    - chair - lamp - elevator - vending_machine - phone_booth - ticket_gate
    - court_document - contract_page - exam_answer_sheet - shipping_label - safety_manual
    - control_panel - dashboard_screen - call_queue - waiting_room - altar_table
    - container_crane - substation_switchgear - hospital_IV_pole - microscope_slide
    - nursery_toy_bin - walker_frame - interview_scorecard - evidence_bag - receipt_stack
    - relay_cabinet - prop_table - cue_sheet - workbench_vise - customs_seal

  SUBJECT:  # シーン/対象（風景・概念寄りも含む）
    - library - server_room - port_terminal - courtroom - operating_room - substation
    - backstage_corridor - rehearsal_stage - recycling_plant - railway_platform
    - shrine_gate - funeral_altar - interview_room - call_center_floor - nursery_classroom
    - lab_bench - fermentation_tank - perfume_workshop - pigment_studio
    - blueprint_sheet - patent_diagram - city_block - bridge - corridor_of_lockers
    - silent_highway - rain_on_window - crowded_market - empty_classroom

  # ===== Materials / States =====
  MATERIAL_OR_STATE:
    - molten_glass - aerogel - obsidian - mercury_liquid - smoke_filament - ice_crystal
    - lava_flow - gelatin - foam_bubbles - wax_drip - paper_origami - cardboard_corrugation
    - rust_scale - concrete_slurry - carbon_fiber_weave - silicone_gel - latex_sheet
    - stainless_brushed - velvet_flock - ceramic_glaze - acrylic_translucent - bioplastic
    - bioluminescent_fungus - salt_crust - sugar_crystal - oil_slick - ink_bleed
    - magnetic_fluid - shattered_porcelain - wet_clay - ash_powder - frost_bloom

  # ===== Synesthesia =====
  SENSATION:
    - low_cello_rumble - peppermint_coolness - burnt_sugar_smell - antiseptic_clean_smell
    - ozone_after_storm - warm_yeast_aroma - incense_smoke_scent - fresh_pencil_shavings
    - static_noise_hiss - velvet_soft_touch - gritty_dust_touch - cold_metal_touch
    - thick_fog_humidity - citrus_zest_spark - bitter_tonic_taste - salty_sea_air
    - fluorescent_light_buzz - muffled_silence - ticking_clock_anxiety - crowded_room_heat
    - lavender_calm - chlorine_pool_smell - hot_coffee_steam - rubber_glove_smell
    - soap_clean_smoothness - paper_dryness - iron_blood_metallic_note - candle_wax_warmth

  # ===== Biomimicry =====
  BIO_STRUCTURE:
    - beetle_shell - coral_branching - leaf_veins - fish_skeleton - honeycomb_cells
    - mycelium_network - pinecone_spiral - bird_feather_barbs - shark_skin_ridges
    - octopus_suction_cups - jellyfish_tentacles - butterfly_wing_scales - bamboo_nodes
    - spider_silk_web - nautilus_chamber - bone_trabeculae - cactus_ribs
    - termite_mound_ventilation - seed_pod_lattice - bark_cracks - sea_urchin_spines
    - ant_colony_tunnels - lotus_leaf_hydrophobic - gill_filaments - mollusk_shell_ribs
    - root_capillaries - insect_compound_eye - coral_polyp_texture - fern_fractal

  # ===== Idioms (literal interpretation) =====
  IDIOM:
    - time_flies - raining_cats_and_dogs - walking_on_eggshells - skeleton_in_the_closet
    - bite_the_bullet - break_the_ice - spill_the_beans - under_the_weather
    - costs_an_arm_and_a_leg - hit_the_sack - on_thin_ice - burning_the_midnight_oil
    - piece_of_cake - elephant_in_the_room - let_the_cat_out_of_the_bag - a_drop_in_the_bucket
    - paint_the_town_red - once_in_a_blue_moon - rule_of_thumb - pull_strings
    - throw_in_the_towel - miss_the_boat - jump_the_gun - hold_your_horses
    - kill_two_birds_one_stone - stick_out_like_sore_thumb - keep_an_eye_on - go_down_in_flames

  # ===== Style contradictions =====
  STYLE_A:
    - ultra_minimal - baroque_opulent - corporate_manual - kids_storybook - clinical_diagram
    - gothic_cathedral - vaporwave - ukiyoe_print - brutalist_concrete - art_deco
    - photoreal_studio - paper_cutout - chalkboard_sketch - schematic_lineart - oil_painting
  STYLE_B:
    - hyperreal_macro - low_poly_3d - watercolor_wash - neon_cyberpunk - vintage_technical
    - monochrome_ink - claymation - blueprint_cyanotype - medieval_illumination - sterile_hospital
    - luxury_advertising - CCTV_security - museum_catalog - comic_halftone - infrared_thermal

  # ===== Affordance inversion =====
  WRONG_FUNCTION:
    - performs_tax_audit - verifies_identity - filters_air - measures_heart_rate - routes_cargo
    - classifies_evidence - administers_exam - negotiates_contracts - conducts_interview
    - dispenses_medication - sterilizes_tools - manages_call_queue - predicts_injury_risk
    - detects_fraud - schedules_railway_routes - balances_power_grid - sorts_recyclables
    - blends_perfume - monitors_fermentation - issues_warnings - records_witness_testimony
    - appraises_damage - calculates_risk_score - seals_containers - stages_scene_changes

  # ===== Manufacturing constraints =====
  CONSTRAINT:
    - single_piece_print - no_supports - snap_fit_only - bent_sheet_metal_only
    - 2_axis_CNC_only - laser_cut_only - dowel_joinery_only - mortise_tenon_only
    - foldable_flat_pack - tool_less_assembly - minimal_fasteners - one_material_only
    - waterproof_sealed - child_safe_no_sharp_edges - medical_grade_cleanable
    - low_poly_mesh_budget - texture_atlas_single - modular_repeatable_parts
    - tolerance_plus_minus_0_2mm - lightweight_under_500g - stackable_storage - repairable_design

  # ===== Procedural rules =====
  RULESET:
    - prime_number_holes - 3_fold_symmetry - 5_fold_symmetry - curvature_monotone_increase
    - thickness_gradient - labels_every_10mm - only_straight_lines - only_circular_arcs
    - nested_layers_7 - void_ratio_40_percent - bolt_pattern_on_circle - fractal_subdivision_3
    - grid_aligned_orthogonal - organic_noise_displacement - tension_compression_dual
    - two_material_interfaces - repeating_module_A_B - negative_space_focus - single_continuous_surface
```

---

## `{THING}` が無くてもいい？への答え（運用ルール）

* **最短で回すなら**：`THING = OBJECT` でOK（破綻しない）
* **セレンディピティを上げるなら**：`THING`を上のように「書類・設備・空間・仕組み」まで広げる
  → `WRONG_FUNCTION` と噛み合って “意外な説明可能性” が出やすいです。

---

## 実務の小ワザ（当たり率を上げる）

* `affordance_inversion`（機能逆転）は、`THING`を「書類/設備/運用物」に寄せると強い
  例：`court_document` が `routes_cargo` する、みたいな奇妙な整合が出る
* `representation_shift`（図面化）は、ドメインが遠くても破綻しにくい（安定枠）
* `hints` は **2個固定**（3個以上は散りがち）

必要なら、あなたの「10軸×6束×8枚＝480」試作用に、**軸ごとに使うプレースホルダの組み合わせ（どれを必須・どれを任意にするか）**も、テンプレとして固定版を作れます。



私の質問：現状でも試作500枚はできるよね？
いったんコーディングAIにこのチャット内容を共有するので、あなたが作ってくれたデータの構造を読み込んでGemini APIを叩き、画像を保存するPythonコード（実行部）を構築してもらうためのプロンプトを教えてください。モデルはgemini-3-pro-image-previewなので間違えないように。ちなみに生成された画像は後からどんなプロンプト（軸やドメイン）で生成されたの確認できる設計だよね？



はい、**現状の雛形（domains + vocab + axis templates）だけで試作500枚は実行可能**です。

また、後から「どの軸・どの束/ドメイン・どの語彙・どのプロンプトで生成されたか」を確認できる設計にできます（必須）。
実装としては、**画像ファイル名だけに埋め込むより、JSONL/SQLiteでメタデータを保存**するのが堅いです。画像と同名の`.json`を並置する方法も簡単で確実です。

以下に、あなたがコーディングAIへ貼り付けるための **指示プロンプト**を用意します。
（※ここでは“実行部”まで作らせる目的なので、細かい要件を強めに書いてあります。）

---

## コーディングAIに渡すプロンプト（コピペ用）

あなたはPythonエンジニアです。以下の仕様で、Gemini API（Google GenAI / Vertex AI どちらでもよいが、実行可能な形で）を呼び出して画像生成し、保存する「実行スクリプト」を構築してください。モデル名は必ず **`gemini-3-pro-image-preview`** を使い、別モデルにしないでください。

### 目的

このチャット内で定義されたデータ構造（domains, vocab, axis templates）を読み込み、試作として **500枚**の画像を生成してローカルに保存する。

### 入力データ（この会話から転記して使う）

* `domains.yaml`：domains配列。各要素に `bundle`, `domain_id`, `context`, `hints(10)` がある。
* `vocab.yaml`：vocab辞書。`OBJECT`, `THING`, `SUBJECT`, `MATERIAL_OR_STATE`, `SENSATION`, `BIO_STRUCTURE`, `IDIOM`, `STYLE_A`, `STYLE_B`, `WRONG_FUNCTION`, `CONSTRAINT`, `RULESET` がある。
* `axis_templates`：10軸分のテンプレート文字列。プレースホルダ例：`{context}`, `{h1}`, `{h2}`, `{OBJECT}` 等。

### 生成ルール（500枚の内訳）

* 基本は **480枚 = 10軸 × 6束 × 8枚**

  * 各生成ごとに、対象束（bundle）内から `domain_id` を1つ選ぶ（束内5ドメインからランダム）。
  * `hints` はそのドメインの10語から **2語だけ**ランダム抽選して `{h1},{h2}` に入れる。
  * 軸テンプレは axis_id に応じて選択し、必要なプレースホルダを `vocab` からランダムに埋める。
* 追加 **20枚**は以下に分ける：

  * 10枚：ミックス枠（軸を2つ混ぜる）。例：`material_paradox + representation_shift` のように、テンプレ2つを結合して1プロンプトにする（ただし情報過多を避けるため最終プロンプトは500〜800文字程度に抑える）。
  * 10枚：リシード枠（480枚の中から、ランダムに選んだ10条件を seed だけ変えて再生成）。※APIがseed指定できない場合は “同条件で別生成” として扱う。

### 重要：再現性・追跡可能性（必須）

各画像について、後から「何で作ったか」を必ず追える設計にすること。

* 画像保存先：`./out/{axis_id}/{bundle}/{domain_id}/`
* ファイル名：`{timestamp}_{index:04d}_{axis_id}_{bundle}_{domain_id}.png` など衝突しない形
* 画像と同名のメタデータJSONを並置（例：`...png` と `...json`）

  * JSONに必ず入れる：
    `run_id`, `index`, `created_at`, `model`, `axis_id`, `bundle`, `domain_id`,
    `template_text`, `final_prompt`, `hints_used`, `vocab_used`（OBJECTなど実際に引いた語）、
    `error`（失敗時）、`retry_count`
  * さらに集計用に `./out/manifest.jsonl` に1行ずつ追記（JSON Lines）
* 画像生成時に返るレスポンス（候補テキスト、safetyなど）が取れるならJSONに保存

### 実行要件

* Python 3.10+ で動く
* 依存は最小（`pyyaml`, `tqdm`, `python-dotenv` 程度まで）
* APIキーは環境変数から読む（例：`GOOGLE_API_KEY` or `GOOGLE_APPLICATION_CREDENTIALS`）
* 失敗時は指数バックオフで最大3回リトライ、ダメならスキップして続行し、errorを記録
* 進捗表示（tqdm）を入れる
* 途中停止しても再開できるようにする（manifestを読み、既に生成済みのindexを飛ばす）

### Gemini API呼び出し

* 画像生成は必ずモデル **`gemini-3-pro-image-preview`**
* 返ってきた画像バイナリ（またはbase64）をPNGで保存する
* もしSDK差異で画像生成の戻りが特殊なら、実装内で吸収すること（例外処理を丁寧に）

### 出力

* `run.py`（単独で実行できるスクリプト）
* もし分割したいなら `config.yaml` / `data/domains.yaml` / `data/vocab.yaml` などを作ってもよい
* 最後に生成成功枚数・失敗枚数・軸/束別の枚数集計を標準出力に出す

### 注意

* モデル名を間違えない（`gemini-3-pro-image-preview` 固定）
* “どの軸・どのドメインで生成したか”が必ず復元できる設計にする
* hintsは毎回2個だけ、contextは必ず入れる

---

## 補足：あなたの質問への確認

> 生成された画像は後からどんなプロンプト（軸やドメイン）で生成されたの確認できる設計だよね？

はい。上の要件の通り、**画像と同名のJSON + manifest.jsonl**を残せば、後から「軸・束・ドメイン・語彙・最終プロンプト」を100%復元できます。
ファイル名に入れるだけだと情報が欠落しやすいので、**JSONを正**にするのが安全です。

必要なら、上のプロンプトに「このチャットの YAML をそのまま貼る」形に整形して渡せるよう、`domains.yaml` と `vocab.yaml` の“最終版”を1つに統合したテンプレも作れます。

