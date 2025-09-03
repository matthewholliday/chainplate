import sqlite3
from datetime import datetime

class MemoryService:
    def __init__(self, db_name="logs.db"): # make it easier to configure the database name for testing or different environments
        self.conn = sqlite3.connect(db_name)
        self._create_table()

    PREAMBLE = "This is a log of all the previous interactions and memories that have been stored in the system. Please use this information to inform your responses and actions."
    END = "This is the end of the memory log. Please ensure that you have taken all relevant information into account before proceeding."
    def _create_table(self):
        """Create log table if it doesn't exist"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

    def create_memory(self, content):
        with self.conn:
            self.conn.execute(
                "INSERT INTO log (content, created_at) VALUES (?, ?)",
                (content, datetime.now().isoformat())
            )

    def get_memories(self):
        """Read all log records, concatenate them, and return as a string with preamble and end."""
        cursor = self.conn.execute("SELECT content, created_at FROM log ORDER BY id")
        logs = [f"[{row[1]}] {row[0]}" for row in cursor.fetchall()]
        memory_log = "\n".join(logs)
        return f"{self.PREAMBLE}\n{memory_log}\n{self.END}" if logs else f"{self.PREAMBLE}\n{self.END}"

    def __del__(self):
        self.conn.close()
