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
