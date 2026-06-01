# Virtual Try-On API

Vertex AI `virtual-try-on-001` と Google Cloud Storage を使い、人物画像と衣服画像からバーチャル試着結果を生成する API です。

## アーキテクチャ

```
GitHub push (main)
    │
    ▼
Cloud Build
    ├── Docker build & push → Artifact Registry
    └── gcloud run deploy → Cloud Run
                                │
                                ├── Vertex AI (virtual-try-on-001)
                                └── GCS (garments / uploads / results)
```

## API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| GET | `/health` | ヘルスチェック |
| GET | `/api/garments` | 衣服一覧取得（GCS `garments/` から） |
| POST | `/api/upload` | 人物画像アップロード（multipart/form-data） |
| POST | `/api/tryon` | バーチャル試着実行 |
| GET | `/` | テスト用 UI |

### POST /api/tryon リクエスト例

```json
{
  "person_gcs_uri": "gs://your-bucket/uploads/uuid.jpg",
  "garment_gcs_uri": "gs://your-bucket/garments/tshirt.jpg"
}
```

## 事前準備

### 必要なもの

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [Docker](https://docs.docker.com/get-docker/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [go-task](https://taskfile.dev/installation/)

### Google Cloud API の有効化

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com
```

### GCS バケットの準備

```bash
# バケット作成（既存のバケットを使う場合は不要）
gsutil mb -l us-central1 gs://YOUR_BUCKET_NAME

# 衣服画像を garments/ プレフィックスにアップロード
gsutil cp your-garment.jpg gs://YOUR_BUCKET_NAME/garments/
```

---

## セットアップ

### 1. 設定ファイルを作成

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

`terraform/terraform.tfvars` を編集：

```hcl
project_id   = "your-gcp-project-id"
region       = "us-central1"
gcs_bucket   = "your-gcs-bucket-name"
github_owner = "your-github-username"
github_repo  = "virtual-try-on-sample"
```

### 2. Cloud Build の GitHub 連携（初回のみ）

Cloud Build コンソールで GitHub リポジトリを接続します：

1. [Cloud Build トリガー](https://console.cloud.google.com/cloud-build/triggers) を開く
2. **リポジトリを接続** → **GitHub (Cloud Build GitHub アプリ)** を選択
3. GitHub にサインインして `virtual-try-on-sample` リポジトリを許可
4. 接続完了後、Terraform でトリガーを管理できます

### 3. Terraform でインフラを構築

```bash
task tf-init
task tf-apply
```

作成されるリソース：
- Artifact Registry リポジトリ
- Cloud Run サービス用サービスアカウント（Vertex AI / GCS 権限付き）
- Cloud Build 用サービスアカウント（Cloud Run / AR 権限付き）
- Cloud Run サービス（初回はプレースホルダーイメージ）
- Cloud Build トリガー（`main` ブランチへの push で発火）

### 4. 初回デプロイ

```bash
git push origin main
```

Cloud Build が自動的に実行され、Cloud Run に最新イメージがデプロイされます。

デプロイ状況は [Cloud Build コンソール](https://console.cloud.google.com/cloud-build/builds) で確認できます。

### 5. サービス URL の確認

```bash
cd terraform && terraform output service_url
```

---

## ローカル開発

```bash
# 依存関係インストール
task install

# 認証
gcloud auth application-default login

# .env 作成
cp .env.example .env
# .env に GCP_PROJECT, GCS_BUCKET を設定

# 開発サーバー起動
task dev
# → http://localhost:8080
```

---

## ディレクトリ構成

```
.
├── app/
│   ├── main.py               # FastAPI エントリーポイント
│   ├── config.py             # 環境変数管理
│   ├── routers/              # API ルーター
│   ├── services/             # GCS / Vertex AI サービス層
│   └── templates/index.html  # テスト用 UI
├── terraform/
│   ├── main.tf               # Cloud Run + AR + SA + IAM
│   ├── cloudbuild.tf         # Cloud Build トリガー
│   ├── variables.tf
│   ├── outputs.tf
│   └── terraform.tfvars.example
├── cloudbuild.yaml           # Cloud Build パイプライン定義
├── Dockerfile
├── Taskfile.yml
└── pyproject.toml
```
