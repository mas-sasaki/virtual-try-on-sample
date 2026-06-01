# ---- Cloud Build サービスアカウント ----

data "google_project" "project" {}

resource "google_service_account" "cloudbuild_sa" {
  account_id   = "${var.service_name}-cb-sa"
  display_name = "Virtual Try-On Cloud Build SA"
}

resource "google_project_iam_member" "cloudbuild_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

resource "google_project_iam_member" "cloudbuild_ar_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# Cloud Build SA が Cloud Run SA として動作できるようにする
resource "google_service_account_iam_member" "cloudbuild_act_as_cloudrun" {
  service_account_id = google_service_account.cloudrun_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# Cloud Build SA に Cloud Build ログ書き込み権限
resource "google_project_iam_member" "cloudbuild_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloudbuild_sa.email}"
}

# ---- Cloud Build トリガー ----
# 前提: Cloud Build コンソールで GitHub App 接続を事前に完了しておくこと
# https://console.cloud.google.com/cloud-build/triggers → リポジトリを接続

resource "google_cloudbuild_trigger" "push_main" {
  project  = var.project_id
  location = var.region
  name     = "${var.service_name}-push-main"

  service_account = google_service_account.cloudbuild_sa.id

  github {
    owner = var.github_owner
    name  = var.github_repo
    push {
      branch = "^main$"
    }
  }

  filename = "cloudbuild.yaml"

  substitutions = {
    _REGION       = var.region
    _AR_REPO      = var.ar_repository_id
    _SERVICE_NAME = var.service_name
    _GCS_BUCKET   = var.gcs_bucket
  }

  depends_on = [
    google_project_iam_member.cloudbuild_run_admin,
    google_project_iam_member.cloudbuild_ar_writer,
  ]
}
