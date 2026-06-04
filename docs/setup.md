# 新規プロジェクトへのセットアップ手順

このガイドは Virtual Try-On を新しい GCP プロジェクトにゼロからデプロイするための手順書です。

## 前提条件

- GCP プロジェクト作成済み（オーナー権限）
- Google Workspace 組織アカウント（IAP で社内限定アクセスに使用）
- `gcloud` CLI インストール・ログイン済み
- `terraform` インストール済み（1.5+）
- `uv` インストール済み（Python パッケージ管理）
- `task` インストール済み（Taskfile runner）
- GitHub アカウント・このリポジトリのフォーク or クローン

---

## Step 1: GCP API 有効化

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  aiplatform.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  compute.googleapis.com \
  iap.googleapis.com
```

---

## Step 2: GCS バケット作成

> ⚠️ GCS バケットは Terraform 管理外です。手動で作成してください。

```bash
gcloud storage buckets create gs://YOUR_BUCKET_NAME \
  --location=asia-northeast1 \
  --uniform-bucket-level-access
```

バケット名はグローバルで一意である必要があります。例: `virtual-try-on-yourcompany`

---

## Step 3: OAuth 同意画面・クライアント設定（手動）

> ⚠️ `google_iap_brand` / `google_iap_client` Terraform リソースは 2025年7月以降廃止のため、コンソールで手動作成します。

### 3-1. OAuth 同意画面の設定

1. [GCP コンソール → APIs & Services → OAuth 同意画面](https://console.cloud.google.com/apis/credentials/consent) を開く
2. ユーザーの種類: **「内部」** を選択（Google Workspace 組織内のみ）
3. アプリ名・サポートメールを入力して保存

### 3-2. OAuth クライアント ID の作成

1. [GCP コンソール → APIs & Services → 認証情報](https://console.cloud.google.com/apis/credentials) を開く
2. 「認証情報を作成」→「OAuth クライアント ID」
3. アプリケーションの種類: **「ウェブ アプリケーション」**
4. 名前: `Virtual Try-On IAP`（任意）
5. 「承認済みのリダイレクト URI」に以下を追加:
   ```
   https://iap.googleapis.com/v1/oauth/clientIds/{後で入力}:handleRedirect
   ```
   ※ CLIENT_ID が確定してから再編集して正式な URI を設定します（Step 9 参照）
6. 「作成」をクリックして **クライアント ID** と **クライアントシークレット** を控える

---

## Step 4: IAP サービスエージェント作成

> ⚠️ Terraform が IAP サービスエージェントに権限を付与する前に、エージェント自体が存在する必要があります。

```bash
gcloud beta services identity create \
  --service=iap.googleapis.com \
  --project=YOUR_PROJECT_ID
```

成功すると以下のようなメッセージが表示されます:
```
Service identity created: service-PROJECT_NUMBER@gcp-sa-iap.iam.gserviceaccount.com
```

---

## Step 5: terraform.tfvars 設定

```bash
cp terraform/terraform.tfvars.example terraform/terraform.tfvars
```

`terraform/terraform.tfvars` を編集して各値を設定:

```hcl
project_id       = "your-gcp-project-id"
region           = "asia-northeast1"
vertex_ai_region = "asia-southeast1"
gcs_bucket       = "your-bucket-name"       # Step 2 で作成したバケット名
github_owner     = "your-github-username"
github_repo      = "virtual-try-on-sample"

# IAP
# ドメインは Step 7 で確定後に変更する場合あり（sslip.io 使用時）
domain                   = "tryon.example.com"
iap_oauth2_client_id     = "xxxxx.apps.googleusercontent.com"  # Step 3 で取得
iap_oauth2_client_secret = "GOCSPX-xxxxxx"                     # Step 3 で取得
iap_members              = ["domain:your-company.com"]          # 社員全員を許可

# GitHub App 連携前は false のままにする
create_cloudbuild_trigger = false
```

> ⚠️ `gcs_bucket` を実際のバケット名に設定し忘れると Cloud Run が起動しても全 API が 500 エラーになります。

### iap_members の書き方

| 対象 | 設定例 |
|------|--------|
| 社員全員（ドメイン） | `["domain:company.com"]` |
| 特定グループ | `["group:dev-team@company.com"]` |
| 特定ユーザー | `["user:alice@company.com"]` |

---

## Step 6: Terraform 初回 apply

```bash
task tf-init
task tf-apply
```

完了後、ロードバランサーの IP アドレスを確認:

```bash
task tf-output
# lb_ip = "x.x.x.x" を控えておく
```

---

## Step 7: ドメイン設定

### Option A: sslip.io（DNS 変更不要、推奨）

会社の DNS を変更できない場合は sslip.io を使います。`<lb_ip>.sslip.io` が自動的にその IP に解決されます。

`terraform/terraform.tfvars` を更新:

```hcl
domain = "x.x.x.x.sslip.io"  # lb_ip の値に置き換える
```

再 apply:

```bash
task tf-apply
```

> ⚠️ ドメイン変更時に SSL 証明書の再作成が必要です。`Error: ssl_certificate resource is already being used` が出た場合は以下を実行してから `task tf-apply`:
> ```bash
> cd terraform
> terraform destroy -target=google_compute_global_forwarding_rule.lb_https -auto-approve
> terraform destroy -target=google_compute_target_https_proxy.lb -auto-approve
> terraform destroy -target=google_compute_managed_ssl_certificate.lb -auto-approve
> ```

### Option B: カスタムドメイン

DNS の A レコードに `lb_ip` を登録してください。設定方法は DNS プロバイダーの管理画面で行います。

---

## Step 8: GitHub App 連携 → Cloud Build トリガー作成

1. [Cloud Build コンソール](https://console.cloud.google.com/cloud-build/triggers) を開く
2. 「リポジトリを接続」→「GitHub (Cloud Build GitHub App)」
3. GitHub でアプリを認可し、対象リポジトリを選択

連携完了後、`terraform/terraform.tfvars` を更新:

```hcl
create_cloudbuild_trigger = true
```

再 apply:

```bash
task tf-apply
```

---

## Step 9: OAuth クライアントの設定を更新

Step 3 で作成した OAuth クライアントを GCP コンソールで編集:

| 項目 | 値 |
|------|-----|
| 承認済みの JavaScript 生成元 | `https://your-domain` |
| 承認済みのリダイレクト URI | `https://iap.googleapis.com/v1/oauth/clientIds/{CLIENT_ID}:handleRedirect` |

`{CLIENT_ID}` は Step 3 で控えたクライアント ID（例: `444xxxxxx.apps.googleusercontent.com`）です。

---

## Step 10: SSL 証明書のアクティベート待機

Managed SSL 証明書のプロビジョニングには最大 20 分かかります。

```bash
gcloud compute ssl-certificates describe virtual-try-on-cert \
  --global --format="value(managed.status)"
```

`ACTIVE` になるまで待機してください。

---

## Step 11: サンプル画像の生成・アップロード

direnv で環境変数を設定してから実行:

```bash
# .envrc に GCP_PROJECT と GCS_BUCKET を設定済みであること
task generate-garments       # 衣服画像（トップス・ボトムス、ジャストサイズ）を生成して GCS にアップロード
task generate-mannequins     # マネキン画像を生成して GCS にアップロード
task generate-fit-variants   # 各衣服のシルエットバリアント（タイト・オーバーサイズ・ゆったり・ボックス）を生成
```

`generate-fit-variants` は既存ファイルをスキップするため、途中で中断しても再実行可能。

---

## Step 12: 初回デプロイ

```bash
git push origin main
```

Cloud Build が自動で起動します。進捗は [Cloud Build コンソール](https://console.cloud.google.com/cloud-build/builds) で確認できます。ビルドには 3〜5 分かかります。

---

## Step 13: 動作確認

1. `https://your-domain` にアクセス
2. IAP の Google ログイン画面が表示される
3. 社内アカウントでログイン
4. マネキン一覧・衣服一覧が表示される
5. マネキンを選択 → 衣服を選択 → 試着結果が表示される

---

## トラブルシューティング

### `invalid_grant` / `reauth related error` が出る

認証トークンが期限切れです。再ログインしてください:

```bash
gcloud auth application-default login
```

### `allUsers` IAM バインディングが org ポリシーでブロックされる

```
Error: Error setting IAM policy: ... POLICY_VIOLATED
```

組織ポリシー `constraints/iam.allowedPolicyMemberDomains` が `allUsers` を禁止しています。Terraform の Cloud Run invoker には IAP サービスエージェント SA を使うよう設計済みのため、Step 4 の IAP サービスエージェント作成が完了していれば自動的に解決されます。

### `Repository mapping does not exist`（Cloud Build トリガー作成失敗）

```
Error: Error creating Trigger: ... Repository mapping does not exist
```

GitHub App 連携が完了していません。Step 8 の手順で Cloud Build コンソールからリポジトリを接続してから再試行してください。

### 全 API が 500 エラー

`terraform.tfvars` の `gcs_bucket` が実際のバケット名になっているか確認してください。プレースホルダー `"your-gcs-bucket-name"` のままだと全 API が失敗します。変更後は `task tf-apply` を実行してください。

### `iap_members` のパースエラー

`TF_VAR_iap_members` 環境変数が設定されている場合、`terraform.tfvars` の値と競合します。`unset TF_VAR_iap_members` してから再実行してください。

### Terraform Lock ファイルの不整合

```
Error: Inconsistent dependency lock file
```

新しい `.tf` ファイルを追加した後に発生します。`task tf-init` を実行してください。
