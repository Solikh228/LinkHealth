import os
from pathlib import Path

# Base backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent

# Helper to load .env file if it exists without extra dependencies
def _load_env_file(filepath: Path) -> None:
    if filepath.is_file():
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

# Check backend/.env and root .env
_load_env_file(BACKEND_DIR / ".env")
_load_env_file(BACKEND_DIR.parent / ".env")

# Database URL configuration (database-agnostic, defaults to SQLite)
# Supports PostgreSQL, MySQL, SQLite, etc.
DEFAULT_DB_FILE = BACKEND_DIR / "subtracker.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_FILE}")

# Normalization for legacy postgres:// URLs
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.getenv("SECRET_KEY", "subtracker-super-secret-jwt-key-2026")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30  # 30 days
