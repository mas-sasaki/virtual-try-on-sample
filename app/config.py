from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gcp_project: str
    gcp_region: str = "us-central1"
    gcs_bucket: str
    gcs_garments_prefix: str = "garments/"
    gcs_uploads_prefix: str = "uploads/"
    gcs_results_prefix: str = "results/"


settings = Settings()
