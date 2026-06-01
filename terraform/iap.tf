# ============================================================
# Identity-Aware Proxy (IAP) + Cloud Load Balancer
# 社内ユーザー限定アクセス制御
# ============================================================

# ---- Static IP ----

resource "google_compute_global_address" "lb" {
  name    = "${var.service_name}-ip"
  project = var.project_id
}

# ---- Managed SSL Certificate ----

resource "google_compute_managed_ssl_certificate" "lb" {
  name    = "${var.service_name}-cert"
  project = var.project_id
  managed {
    domains = [var.domain]
  }
}

# ---- Serverless NEG (Cloud Run へのルーティング) ----

resource "google_compute_region_network_endpoint_group" "cloudrun_neg" {
  name                  = "${var.service_name}-neg"
  project               = var.project_id
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.service.name
  }
}

# ---- IAP Brand ----
# 注意: プロジェクトに既に IAP Brand が存在する場合は import が必要
#   terraform import google_iap_brand.default \
#     projects/PROJECT_NUMBER/brands/PROJECT_NUMBER
# PROJECT_NUMBER の確認: gcloud projects describe PROJECT_ID --format="value(projectNumber)"

resource "google_iap_brand" "default" {
  support_email     = var.iap_support_email
  application_title = "Virtual Try-On"
  project           = var.project_id

  lifecycle {
    # IAP Brand は削除できないため destroy をスキップ
    prevent_destroy = true
  }
}

# ---- IAP OAuth2 クライアント ----

resource "google_iap_client" "default" {
  display_name = "Virtual Try-On IAP Client"
  brand        = google_iap_brand.default.name
}

# ---- Backend Service (IAP 有効) ----

resource "google_compute_backend_service" "lb" {
  name    = "${var.service_name}-backend"
  project = var.project_id

  backend {
    group = google_compute_region_network_endpoint_group.cloudrun_neg.id
  }

  iap {
    enabled              = true
    oauth2_client_id     = google_iap_client.default.client_id
    oauth2_client_secret = google_iap_client.default.secret
  }

  log_config {
    enable = false
  }
}

# ---- URL Map (HTTPS) ----

resource "google_compute_url_map" "lb" {
  name            = "${var.service_name}-urlmap"
  project         = var.project_id
  default_service = google_compute_backend_service.lb.id
}

# ---- URL Map (HTTP → HTTPS リダイレクト) ----

resource "google_compute_url_map" "redirect" {
  name    = "${var.service_name}-http-redirect"
  project = var.project_id

  default_url_redirect {
    https_redirect         = true
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
    strip_query            = false
  }
}

# ---- HTTPS Proxy ----

resource "google_compute_target_https_proxy" "lb" {
  name             = "${var.service_name}-https-proxy"
  project          = var.project_id
  url_map          = google_compute_url_map.lb.id
  ssl_certificates = [google_compute_managed_ssl_certificate.lb.id]
}

# ---- HTTP Proxy (リダイレクト用) ----

resource "google_compute_target_http_proxy" "redirect" {
  name    = "${var.service_name}-http-proxy"
  project = var.project_id
  url_map = google_compute_url_map.redirect.id
}

# ---- Forwarding Rules ----

resource "google_compute_global_forwarding_rule" "lb_https" {
  name       = "${var.service_name}-https"
  project    = var.project_id
  target     = google_compute_target_https_proxy.lb.id
  port_range = "443"
  ip_address = google_compute_global_address.lb.address
}

resource "google_compute_global_forwarding_rule" "lb_http" {
  name       = "${var.service_name}-http"
  project    = var.project_id
  target     = google_compute_target_http_proxy.redirect.id
  port_range = "80"
  ip_address = google_compute_global_address.lb.address
}

# ---- IAP アクセス権付与 ----

resource "google_iap_web_backend_service_iam_binding" "access" {
  project             = var.project_id
  web_backend_service = google_compute_backend_service.lb.name
  role                = "roles/iap.httpsResourceAccessor"
  members             = var.iap_members
}
