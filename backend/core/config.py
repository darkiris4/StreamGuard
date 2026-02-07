from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./streamguard.db"
    database_url_sync: str = "sqlite:///./streamguard.db"
    cac_github_url: str = "https://github.com/ComplianceAsCode/content"
    cac_release_version: str = "latest"
    offline_mode: bool = False
    ssh_key_path: str = ""
    ssh_user: str = "root"
    max_concurrent_hosts: int = 10
    ansible_inventory: str = ""
    base_iso_urls: str = ""
    cors_origins: str = "*"

    @property
    def cors_allow_origins(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
