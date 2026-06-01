terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

locals {
  image_url = "${var.region}-docker.pkg.dev/${var.project_id}/${var.ar_repository_id}/${var.service_name}"
}

# ---- Artifact Registry ----

resource "google_artifact_registry_repository" "repo" {
  repository_id = var.ar_repository_id
  location      = var.region
  format        = "DOCKER"
  description   = "Virtual Try-On Docker images"
}

# ---- Cloud Run サービスアカウント ----

resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.service_name}-run-sa"
  display_name = "Virtual Try-On Cloud Run SA"
}

resource "google_project_iam_member" "cloudrun_vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "cloudrun_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

# ---- Cloud Run ----

resource "google_cloud_run_v2_service" "service" {
  name     = var.service_name
  location = var.region

  deletion_protection = false

  template {
    service_account = google_service_account.cloudrun_sa.email

    containers {
      # 初回は Cloud Build が未実行のためプレースホルダーを使用
      # 最初の push 後に Cloud Build が自動更新する
      image = "us-docker.pkg.dev/cloudrun/container/hello:latest"

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "VERTEX_AI_REGION"
        value = var.vertex_ai_region
      }
      env {
        name  = "GCS_BUCKET"
        value = var.gcs_bucket
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    timeout = "120s"
  }

  # LB 経由のトラフィックのみ受け付ける（直接 URL アクセスを遮断）
  ingress = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  lifecycle {
    # image は Cloud Build が管理するため Terraform の差分を無視
    ignore_changes = [template[0].containers[0].image]
  }
}

# allUsers を維持しつつ ingress 制限でネットワーク制御
# 実際の認証は IAP (iap.tf) が担当する
resource "google_cloud_run_v2_service_iam_member" "lb_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
