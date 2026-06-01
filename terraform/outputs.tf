output "service_url" {
  description = "Cloud Run サービスの URL"
  value       = google_cloud_run_v2_service.service.uri
}

output "artifact_registry_url" {
  description = "Artifact Registry のリポジトリ URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${var.ar_repository_id}"
}

output "image_url" {
  description = "Docker イメージの完全 URL（タグなし）"
  value       = local.image_url
}

output "cloudrun_service_account" {
  description = "Cloud Run 実行用サービスアカウント"
  value       = google_service_account.cloudrun_sa.email
}

output "cloudbuild_service_account" {
  description = "Cloud Build 用サービスアカウント"
  value       = google_service_account.cloudbuild_sa.email
}
