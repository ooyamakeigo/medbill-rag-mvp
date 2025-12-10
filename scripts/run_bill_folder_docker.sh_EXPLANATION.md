# `run_bill_folder_docker.sh` スクリプトの詳細説明

## コマンド概要

```bash
bash scripts/run_bill_folder_docker.sh ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7
```

このコマンドは、医療費請求書（Medical Bill）を処理するためのパイプラインをDockerコンテナ内で実行します。

---

## 実行される処理の全体フロー

### ステップ1: スクリプトの初期チェック

1. **引数の検証**
   - `ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7` という `BILL_ID`（請求書フォルダID）が引数として渡されているか確認
   - 引数がなければエラーメッセージを表示して終了

2. **作業ディレクトリの移動**
   - スクリプトの場所から見て、プロジェクトのルートディレクトリ（`medbill-rag-mvp/`）に移動

3. **環境変数ファイル（`.env`）の確認**
   - `.env` ファイルが存在するか確認
   - 存在しない場合は、エラーメッセージを表示して終了
   - `.env` には以下のような設定が含まれます：
     - `PROJECT_ID`: Google Cloud プロジェクトID
     - `BUCKET_CASE`: 医療費請求書が保存されているGCSバケット名
     - `MODEL_ID`: 使用するAIモデル（デフォルト: `gemini-2.5-flash`）
     - その他の設定値

### ステップ2: Dockerイメージのビルド

```bash
docker build -t medbill-rag-mvp:latest .
```

- **目的**: アプリケーションを実行するためのDockerイメージを作成
- **処理内容**:
  1. `Dockerfile` に基づいてイメージをビルド
  2. Python 3.11のスリム版ベースイメージを使用
  3. `requirements.txt` に記載されたPythonパッケージをインストール
  4. `src/` ディレクトリ（アプリケーションコード）をコピー
  5. `rag_base/` ディレクトリ（RAG用のベース知識ベース）をコピー
- **注意**: 初回実行時や `Dockerfile` が変更された場合のみ実行される（既存イメージがあればスキップされる場合もある）

### ステップ3: Dockerコンテナの実行

```bash
docker run --rm \
  --env-file .env \
  -e BILL_FOLDER_ID="ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7" \
  medbill-rag-mvp:latest
```

- **`--rm`**: コンテナ終了後に自動的に削除
- **`--env-file .env`**: `.env` ファイルの内容を環境変数としてコンテナに渡す
- **`-e BILL_FOLDER_ID=...`**: 処理対象の請求書フォルダIDを環境変数として設定

### ステップ4: Pythonアプリケーションの実行

コンテナ内で `python -m medbill_rag` が実行され、以下の処理が順番に実行されます：

#### 4-1. ファイルの検出と選択

- **場所**: `gs://<BUCKET_CASE>/bills/ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7/`
- **検索対象**:
  - `eob.pdf` (Explanation of Benefits: 給付金説明書)
  - `itemized_bill.pdf` (明細請求書)
  - `statement.pdf` (請求明細書)
- **処理**: 各タイプのファイルを検出し、最適なファイルを選択

#### 4-2. OCR（光学文字認識）処理

- **使用サービス**: Google Cloud Document AI
- **処理内容**: 各PDFファイルをOCRでテキスト化
  - EOB → `eob_text`
  - Itemized Bill → `itemized_text`
  - Statement → `statement_text`

#### 4-3. 構造化データの抽出

- **使用AI**: Vertex AI Gemini モデル
- **抽出される情報**:
  - `provider_name`: 医療機関名
  - `provider_state`: 医療機関の州
  - `payer_name`: 保険会社名
  - `plan_name`: 保険プラン名
  - `dos_from` / `dos_to`: 診療日（Date of Service）の範囲
  - `total_charge`: 総請求額
  - `patient_responsibility`: 患者負担額
  - `doc_type`: 文書タイプ

#### 4-4. オーバーレイ知識ベースの準備

- **目的**: 医療機関や保険会社固有の情報を取得（MVPでは空のまま）
- **処理**:
  - 医療機関名から `hospital_id` を取得
  - 保険会社名から `payer_id` を取得

#### 4-5. RAG（Retrieval-Augmented Generation）による分析

- **知識ベースの読み込み**:
  - `rag_base/`: 非PHI（個人情報を含まない）のベース知識ベースをローカルから読み込み
  - オーバーレイ知識ベース: MVPでは空（将来拡張用）
- **プロンプトの構築**:
  - OCRで取得したテキスト（EOB、Itemized、Statement）
  - 抽出したメタデータ
  - 知識ベースの情報
  - これらを組み合わせて、請求書の分析用プロンプトを作成
- **AI分析の実行**:
  - Vertex AI Gemini モデルを使用して、請求書の問題点や異常を分析
  - 結果はJSON形式で返される（`findings.json`）

#### 4-6. レポートとメールドラフトの生成

1. **`findings.json` の生成と保存**
   - AI分析結果をJSON形式で保存
   - 保存先: `gs://<BUCKET_CASE>/bills/ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7/outputs/findings.json`

2. **`report.md` の生成と保存**
   - 分析結果をMarkdown形式のレポートに変換
   - 保存先: `gs://<BUCKET_CASE>/bills/ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7/outputs/report.md`

3. **`email_draft.txt` の生成と保存**
   - ユーザー向けのメールドラフトを生成
   - 保存先: `gs://<BUCKET_CASE>/bills/ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7/outputs/email_draft.txt`

### ステップ5: 完了メッセージの表示

スクリプトは最後に、出力ファイルの保存場所を表示します：

```
✅ Done. Check outputs in GCS:
   gs://<BUCKET_CASE>/bills/ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7/outputs/
```

---

## 出力ファイルの説明

処理が完了すると、以下の3つのファイルがGCSに保存されます：

1. **`findings.json`**
   - AIが検出した請求書の問題点や異常を構造化したJSON形式のデータ
   - 例: 請求額の不一致、保険適用の誤り、重複請求など

2. **`report.md`**
   - `findings.json` の内容を人間が読みやすいMarkdown形式のレポートに変換したもの
   - 請求書の概要、検出された問題点、推奨事項などが含まれる

3. **`email_draft.txt`**
   - 保険会社や医療機関に問い合わせる際のメールドラフト
   - 検出された問題点を説明し、対応を依頼する内容

---

## 技術スタック

- **コンテナ**: Docker
- **言語**: Python 3.11
- **OCR**: Google Cloud Document AI
- **AI分析**: Vertex AI Gemini 2.5 Flash
- **ストレージ**: Google Cloud Storage (GCS)
- **アーキテクチャ**: RAG（Retrieval-Augmented Generation）

---

## 前提条件

1. **Google Cloud プロジェクトの設定**
   - Document AI API が有効
   - Vertex AI API が有効
   - 適切な権限（GCSへの読み書き、Document AI、Vertex AIの使用）

2. **環境変数の設定**
   - `.env` ファイルに必要な設定値が記入されている

3. **GCSバケットの準備**
   - 指定された `BILL_ID` のフォルダが存在し、PDFファイルがアップロードされている

4. **Dockerのインストール**
   - Dockerがインストールされ、実行可能な状態であること

---

## エラーが発生した場合

- **`.env` が見つからない**: `.env.example` をコピーして `.env` を作成し、必要な値を設定
- **Dockerイメージのビルドエラー**: `Dockerfile` や `requirements.txt` に問題がないか確認
- **GCSアクセスエラー**: Google Cloud の認証情報と権限を確認
- **ファイルが見つからない**: 指定された `BILL_ID` のフォルダがGCSに存在するか確認


