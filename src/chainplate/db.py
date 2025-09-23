# src/chainplate/services/data/db.py
import sqlite3
import threading
import os
import logging
from contextlib import contextmanager
from pathlib import Path

# Resolve DB path from environment (default chainplate.db in CWD or configured dir)
_DEFAULT_DB = os.getenv("CHAINPLATE_DB", "chainplate.db")
_DB_PATH = Path(_DEFAULT_DB)

def _ensure_parent_dir(path: Path):
    try:
        parent = path.parent
        if parent and not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fail silently; sqlite connect will raise if truly invalid
        pass

_ensure_parent_dir(_DB_PATH)

# Thread-local holder so each thread keeps its own connection
_thread_state = threading.local()

_logger = logging.getLogger("chainplate.db")

def _new_connection() -> sqlite3.Connection:
    """Create a new sqlite3 connection.

    Adds resiliency for environments (e.g. Windows bind mounts / network filesystems)
    where WAL mode may not be supported. Falls back to DELETE journal mode if
    enabling WAL raises an OperationalError like 'unable to open database file'.
    """
    global _DB_PATH
    # Re-evaluate env in case changed at runtime (rare but keeps flexible)
    env_path = os.getenv("CHAINPLATE_DB")
    if env_path and Path(env_path) != _DB_PATH:
        _DB_PATH = Path(env_path)
        _ensure_parent_dir(_DB_PATH)

    try:
        conn = sqlite3.connect(_DB_PATH, isolation_level=None)  # autocommit
    except sqlite3.OperationalError as e:  # pragma: no cover - defensive
        # Provide clearer diagnostics for troubleshooting volume/permission issues
        raise sqlite3.OperationalError(
            f"Failed to open sqlite database at '{_DB_PATH}'. "
            f"Parent exists={_DB_PATH.parent.exists()} cwd='{os.getcwd()}' error={e}"
        ) from e

    conn.row_factory = sqlite3.Row

    # Attempt WAL unless explicitly disabled
    disable_wal = os.getenv("CHAINPLATE_DISABLE_WAL", "0") in {"1", "true", "True"}
    if not disable_wal:
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
        except sqlite3.OperationalError as wal_err:  # pragma: no cover - depends on FS
            # Fallback to DELETE mode (default) for filesystems not supporting WAL
            try:
                conn.execute("PRAGMA journal_mode=DELETE;")
            except Exception:  # pragma: no cover - highly unlikely
                pass
            _logger.warning(
                "WAL mode unsupported for '%s' (%s); fell back to DELETE journaling.",
                _DB_PATH,
                wal_err,
            )
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def _get_connection() -> sqlite3.Connection:
    conn = getattr(_thread_state, "conn", None)
    if conn is None:
        conn = _new_connection()
        _thread_state.conn = conn
    return conn

@contextmanager
def db_cursor():
    """
    Usage:
        with db_cursor() as cur:
            cur.execute("INSERT INTO ...", params)
    """
    conn = _get_connection()
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()

def set_db_path(new_path: str):
    """Programmatically override the database path (used by DataService)."""
    global _DB_PATH
    _DB_PATH = Path(new_path)
    _ensure_parent_dir(_DB_PATH)
    # Close existing thread-local connection so it reopens with new path
    if getattr(_thread_state, "conn", None):
        try:
            _thread_state.conn.close()
        except Exception:
            pass
        _thread_state.conn = None
