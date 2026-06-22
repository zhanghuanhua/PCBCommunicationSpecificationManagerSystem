import os
from pathlib import Path


BASE_DIR = Path(os.getenv("EAP_SYSTEM_HOME", ".")).resolve()
DATA_DIR = Path(os.getenv("EAP_DATA_DIR", BASE_DIR / "data")).resolve()
EXPORT_DIR = Path(os.getenv("EAP_EXPORT_DIR", BASE_DIR / "exports")).resolve()
UPLOAD_DIR = Path(os.getenv("EAP_UPLOAD_DIR", BASE_DIR / "uploads")).resolve()
TEMPLATE_DIR = Path(os.getenv("EAP_TEMPLATE_DIR", UPLOAD_DIR / "templates")).resolve()
EXPORT_SETTINGS_PATH = DATA_DIR / "export_settings.json"


def ensure_runtime_dirs() -> None:
    for path in (DATA_DIR, EXPORT_DIR, UPLOAD_DIR, TEMPLATE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def sqlite_database_url() -> str:
    configured = os.getenv("DATABASE_URL", "").strip()
    if configured:
        return configured
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{(DATA_DIR / 'interface_manager.db').as_posix()}"
