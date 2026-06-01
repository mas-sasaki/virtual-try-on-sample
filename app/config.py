from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gcp_project: str
    gcp_region: str = "asia-northeast1"
    vertex_ai_region: str = "asia-southeast1"
    gcs_bucket: str
    gcs_garments_prefix: str = "garments/"
    gcs_uploads_prefix: str = "uploads/"
    gcs_results_prefix: str = "results/"


settings = Settings()
