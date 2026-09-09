import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import tempfile

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _is_writable_dir(path: str) -> bool:
    try:
        testfile = os.path.join(path, ".sqlite_write_check")
        with open(testfile, "w") as f:
            f.write("1")
        os.remove(testfile)
        return True
    except Exception:
        return False


if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Handle SQLite paths (relative paths, default, or when in read-only environment like Vercel)
if not DATABASE_URL or DATABASE_URL.startswith("sqlite"):
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or not _is_writable_dir("."):
        db_file = os.path.join(tempfile.gettempdir(), "resortiq.db")
        DATABASE_URL = f"sqlite:///{db_file.replace(os.sep, '/')}"
    elif not DATABASE_URL:
        DATABASE_URL = "sqlite:///./resortiq.db"

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

_initialized = False


def get_db():
    global _initialized
    if not _initialized:
        try:
            Base.metadata.create_all(bind=engine)
            from seed import ensure_seeded
            ensure_seeded()
            _initialized = True
        except Exception as e:
            print(f"DB init warning: {e}")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
