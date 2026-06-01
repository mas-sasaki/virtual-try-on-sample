# Virtual Try-On API 設計資料

## 1. システム概要

Vertex AI の `virtual-try-on-001` モデルを使い、人物画像と衣服画像からバーチャル試着結果を生成する API。

---

## 2. アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│ 開発者                                                       │
│   git push (main)                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Cloud Build (asia-northeast1)                                │
│   1. docker build                                            │
│   2. docker push → Artifact Registry                        │
│   3. gcloud run deploy → Cloud Run                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Cloud Run (asia-northeast1)  ← FastAPI アプリ               │
│                                                              │
│  GET  /api/garments   ──────────────────────────┐           │
│  POST /api/upload     ──────────────────────┐   │           │
│  POST /api/tryon      ──────────────┐       │   │           │
│  GET  /api/image      ─────────┐   │       │   │           │
│  GET  /               (UI)     │   │       │   │           │
└────────────────────────────────┼───┼───────┼───┼───────────┘
                                 │   │       │   │
              ┌──────────────────┘   │       │   │
              │  画像プロキシ取得     │       │   │
              ▼                      ▼       ▼   ▼
┌────────────────────────┐   ┌──────────────────────────────┐
│ Vertex AI              │   │ Cloud Storage                 │
│ (asia-southeast1)      │   │ (asia-northeast1)             │
│                        │   │                               │
│ virtual-try-on-001     │   │ garments/   ← 衣服画像        │
│ imagen-3.0-generate-001│   │ uploads/    ← 人物画像        │
│                        │   │ results/    ← 試着結果        │
└────────────────────────┘   └──────────────────────────────┘
```

---

## 3. 有効化が必要な GCP API

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com
```

| API | 用途 |
|-----|------|
| `aiplatform.googleapis.com` | Vertex AI (Virtual Try-On / Imagen) |
| `run.googleapis.com` | Cloud Run |
| `artifactregistry.googleapis.com` | Docker イメージ管理 |
| `cloudbuild.googleapis.com` | CI/CD パイプライン |
| `storage.googleapis.com` | GCS |

---

## 4. IAM 権限

### 4-1. ローカル開発（ユーザーアカウント）

```bash
gcloud auth application-default login
```

| ロール | 用途 |
|--------|------|
| `roles/aiplatform.user` | Vertex AI API 呼び出し |
| `roles/storage.objectAdmin` | GCS 読み書き |

### 4-2. Cloud Run サービスアカウント（Terraform が自動作成）

アカウント名: `virtual-try-on-run-sa@PROJECT.iam.gserviceaccount.com`

| ロール | 用途 |
|--------|------|
| `roles/aiplatform.user` | Vertex AI API 呼び出し |
| `roles/storage.objectAdmin` | GCS 読み書き |

### 4-3. Cloud Build サービスアカウント（Terraform が自動作成）

アカウント名: `virtual-try-on-cb-sa@PROJECT.iam.gserviceaccount.com`

| ロール | 用途 |
|--------|------|
| `roles/run.admin` | Cloud Run デプロイ |
| `roles/artifactregistry.writer` | Docker イメージ push |
| `roles/logging.logWriter` | ビルドログ書き込み |
| `roles/iam.serviceAccountUser` | Cloud Run SA として動作 |

---

## 5. 環境変数

### アプリケーション（Cloud Run / ローカル）

| 変数名 | 必須 | デフォルト | 説明 |
|--------|------|-----------|------|
| `GCP_PROJECT` | ✓ | — | GCP プロジェクト ID |
| `GCS_BUCKET` | ✓ | — | GCS バケット名 |
| `GCP_REGION` | | `asia-northeast1` | Cloud Run のリージョン |
| `VERTEX_AI_REGION` | | `asia-southeast1` | Vertex AI API のリージョン |
| `GCS_GARMENTS_PREFIX` | | `garments/` | 衣服画像の GCS プレフィックス |
| `GCS_UPLOADS_PREFIX` | | `uploads/` | アップロード先プレフィックス |
| `GCS_RESULTS_PREFIX` | | `results/` | 試着結果の保存先プレフィックス |

### ローカル開発（`.envrc`）

```bash
use flake

export GCP_PROJECT=your-project-id
export GCS_BUCKET=your-bucket-name
export GCP_REGION=asia-northeast1
export VERTEX_AI_REGION=asia-southeast1
```

### Terraform (`terraform/terraform.tfvars`)

```hcl
project_id       = "your-project-id"
region           = "asia-northeast1"
vertex_ai_region = "asia-southeast1"
gcs_bucket       = "your-bucket-name"
github_owner     = "your-github-username"
github_repo      = "virtual-try-on-sample"
```

---

## 6. GCS バケット構成

```
gs://BUCKET_NAME/
├── garments/
│   ├── tops/          ← 衣服（上）画像
│   └── bottoms/       ← 衣服（下）画像
├── uploads/           ← ユーザーがアップロードした人物画像（自動生成）
└── results/           ← 試着結果画像（自動生成）
```

バケット作成:

```bash
gcloud storage buckets create gs://BUCKET_NAME --location=asia-northeast1
```

---

## 7. リージョン選定の理由

| リソース | リージョン | 理由 |
|---------|-----------|------|
| Cloud Run | `asia-northeast1`（東京）| エンドユーザーへの低レイテンシ |
| Artifact Registry | `asia-northeast1`（東京）| Cloud Run と同一リージョン |
| GCS バケット | `asia-northeast1`（東京）| Cloud Run と同一リージョンでの高速アクセス |
| Vertex AI | `asia-southeast1`（シンガポール）| `virtual-try-on-001` / `imagen-3.0-generate-001` が `asia-northeast1` 未対応 |

---

## 8. デプロイフロー

### 初回セットアップ

```
1. GCP API 有効化
   └─ gcloud services enable ...

2. GCS バケット作成
   └─ gcloud storage buckets create gs://BUCKET --location=asia-northeast1

3. Cloud Build の GitHub App 連携（コンソールで手動）
   └─ https://console.cloud.google.com/cloud-build/triggers
      → リポジトリを接続 → GitHub (Cloud Build GitHub App)

4. Terraform でインフラ構築
   └─ task tf-init && task tf-apply
      作成リソース:
        - Artifact Registry リポジトリ
        - Cloud Run サービスアカウント + IAM
        - Cloud Build サービスアカウント + IAM
        - Cloud Run サービス（初回はプレースホルダー）
        - Cloud Build トリガー（main push で発火）

5. 衣服サンプル画像の生成・アップロード
   └─ task generate-garments

6. 初回デプロイ
   └─ git push origin main
      Cloud Build が自動実行され Cloud Run に反映
```

### 以降のデプロイ

```
git push origin main  →  Cloud Build  →  Cloud Run（自動）
```

---

## 9. API エンドポイント仕様

### GET /health

ヘルスチェック。

**Response**
```json
{"status": "ok"}
```

---

### GET /api/garments

GCS の `garments/` 配下の衣服一覧を返す。

**Response**
```json
[
  {
    "name": "tops/white-tshirt.png",
    "gcs_uri": "gs://bucket/garments/tops/white-tshirt.png",
    "image_url": "/api/image?uri=gs%3A%2F%2F..."
  }
]
```

---

### POST /api/upload

人物画像をアップロードし GCS に保存する。

**Request** `multipart/form-data`

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `file` | File | JPEG または PNG 画像 |

**Response**
```json
{
  "gcs_uri": "gs://bucket/uploads/uuid.jpg",
  "image_url": "/api/image?uri=gs%3A%2F%2F..."
}
```

---

### POST /api/tryon

Virtual Try-On API を呼び出し、試着結果を返す。

**Request** `application/json`

```json
{
  "person_gcs_uri": "gs://bucket/uploads/uuid.jpg",
  "garment_gcs_uri": "gs://bucket/garments/tops/white-tshirt.png"
}
```

**Response**
```json
{
  "result_url": "/api/image?uri=gs%3A%2F%2F...",
  "result_gcs_uri": "gs://bucket/results/uuid.png"
}
```

**エラーレスポンス**

| ステータス | 説明 |
|-----------|------|
| `400` | GCS から画像を取得できない |
| `502` | Vertex AI API エラー |

---

### GET /api/image

GCS オブジェクトをプロキシ配信する。

**Query Parameters**

| パラメータ | 説明 |
|-----------|------|
| `uri` | `gs://` 形式の GCS URI |

**Response** 画像バイナリ（`image/jpeg` または `image/png`）

---

## 10. 技術スタック

| カテゴリ | 採用技術 | バージョン |
|---------|---------|-----------|
| 言語 | Python | 3.12+ |
| Web フレームワーク | FastAPI | 0.115+ |
| ASGI サーバー | Uvicorn | 0.32+ |
| パッケージ管理 | uv | — |
| 開発環境 | Nix + direnv | — |
| コンテナ | Docker | — |
| IaC | Terraform | 1.5+ |
| CI/CD | Cloud Build | — |
| AI モデル（試着） | Vertex AI `virtual-try-on-001` | — |
| AI モデル（画像生成） | Vertex AI `imagen-3.0-generate-001` | — |
| ストレージ | Cloud Storage | — |
| 実行環境 | Cloud Run v2 | — |
