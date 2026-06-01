variable "project_id" {
  description = "Google Cloud プロジェクト ID"
  type        = string
}

variable "region" {
  description = "Cloud Run / Artifact Registry のリージョン"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket" {
  description = "GCS バケット名（衣服画像・結果画像の格納先）"
  type        = string
}

variable "image_url" {
  description = "Artifact Registry に格納した Docker イメージ URL"
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
