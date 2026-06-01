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

# ---- Artifact Registry ----

resource "google_artifact_registry_repository" "repo" {
  repository_id = var.ar_repository_id
  location      = var.region
  format        = "DOCKER"
  description   = "Virtual Try-On Docker images"
}

# ---- Service Account ----

resource "google_service_account" "cloudrun_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Virtual Try-On Cloud Run SA"
}

resource "google_project_iam_member" "vertex_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloudrun_sa.email}"
}

resource "google_project_iam_member" "storage_admin" {
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
      image = var.image_url

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
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
}

# パブリックアクセス（検証用）
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
