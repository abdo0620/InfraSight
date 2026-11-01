from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")   # old .env lines (AI_PROVIDER...) are ignored
    meta_api_key: str = ""             # from dev.meta.ai
    meta_base_url: str = "https://api.meta.ai/v1"
    model_quick: str = ""              # intake triage. Empty: muse-spark-1.1 (see services/ai.py)
    model_default: str = ""            # full report, stage assist
    model_image: str = ""              # repair preview (Muse Image). Empty: muse-image-1.0
    database_url: str = "sqlite:///./infrasight.db"   # swap for postgresql+psycopg://... in production
    upload_dir: str = "uploads"
    max_image_mb: int = 8
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:5173",          # other dev servers that
                               "http://127.0.0.1:5500", "http://localhost:5500"]         # serve the frontend (5500: VS Code Live Server)
    secret_key: str = ""               # signs login tokens and photo links. Empty: random per start (dev only)
    token_hours: int = 12
    ai_calls_per_hour: int = 30        # per user, all AI features together
    sam_url: str = ""                  # own SAM 3.1 server (sam_server/), e.g. http://gpu-box:8100. Empty: SAM 3.1 on the
                                       # Meta Model API (needs META_API_KEY)
    overpass_urls: list[str] = ["https://overpass-api.de/api/interpreter",          # road network for detours,
                                "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]  # tried in order
    duplicate_radius_m: int = 80       # a new report this close to an open ticket may be merged into it
    seed_demo: bool = False            # create the sample tickets on an empty database
    demo_password: str = ""            # if set with seed_demo, also create users citizen / tech / elected


settings = Settings()
