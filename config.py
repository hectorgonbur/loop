import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Cambiar a PostgreSQL en producción: "postgresql://user:pass@localhost/dbname"
DATABASE_URL = "sqlite:///" + str(BASE_DIR / "archihub.db")
