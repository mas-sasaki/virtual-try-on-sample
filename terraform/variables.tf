variable "project_id" {
  description = "Google Cloud プロジェクト ID"
  type        = string
}

variable "region" {
  description = "Cloud Run / Artifact Registry / Cloud Build のリージョン"
  type        = string
  default     = "asia-northeast1"
}

variable "vertex_ai_region" {
  description = "Vertex AI Virtual Try-On API のリージョン（asia-northeast1 未対応のため asia-southeast1 推奨）"
  type        = string
  default     = "asia-southeast1"
}

variable "gcs_bucket" {
  description = "GCS バケット名（衣服画像・結果画像の格納先）"
  type        = string
}

variable "service_name" {
  description = "Cloud Run サービス名"
  type        = string
  default     = "virtual-try-on"
}

variable "ar_repository_id" {
  description = "Artifact Registry リポジトリ ID"
  type        = string
  default     = "virtual-try-on"
}

variable "github_owner" {
  description = "GitHub リポジトリのオーナー名"
  type        = string
}

variable "github_repo" {
  description = "GitHub リポジトリ名"
  type        = string
}

variable "create_cloudbuild_trigger" {
  description = "Cloud Build トリガーを作成するか。GitHub App 接続完了後に true に変更して再 apply する"
  type        = bool
  default     = false
}

variable "domain" {
  description = "カスタムドメイン（IAP + LB 用、例: tryon.company.com）"
  type        = string
}

variable "iap_oauth2_client_id" {
  description = "IAP 用 OAuth2 クライアント ID（GCP コンソールで手動作成）"
  type        = string
}

variable "iap_oauth2_client_secret" {
  description = "IAP 用 OAuth2 クライアントシークレット（GCP コンソールで手動作成）"
  type        = string
  sensitive   = true
}

variable "iap_members" {
  description = <<-EOT
    IAP アクセスを許可するメンバーリスト。形式の例:
      社員全員 (Google Workspace ドメイン): ["domain:company.com"]
      特定ユーザー:                          ["user:alice@company.com", "user:bob@company.com"]
      Google グループ:                       ["group:dev-team@company.com"]
  EOT
  type        = list(string)
}
