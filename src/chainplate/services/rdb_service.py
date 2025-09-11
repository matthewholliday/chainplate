import sqlite3
import uuid
from datetime import datetime

# --- Database Setup (run once) ---
def init_db(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            message_order INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    conn.commit()


# --- 1. Function to create a conversation ---
def create_conversation(conn):
    conversation_id = str(uuid.uuid4())  # unique ID
    timestamp = datetime.utcnow().isoformat()
    
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO conversations (id, created_at)
        VALUES (?, ?)
    """, (conversation_id, timestamp))
    
    conn.commit()
    return conversation_id


# --- 2. Function to create a message in a conversation ---
def add_message(conn, conversation_id, role, content):
    timestamp = datetime.utcnow().isoformat()
    cur = conn.cursor()
    
    # Find the next order number within this conversation
    cur.execute("""
        SELECT COALESCE(MAX(message_order), 0) + 1
        FROM messages
        WHERE conversation_id = ?
    """, (conversation_id,))
    next_order = cur.fetchone()[0]
    
    cur.execute("""
        INSERT INTO messages (conversation_id, role, content, message_order, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (conversation_id, role, content, next_order, timestamp))
    
    conn.commit()
    return cur.lastrowid  # return the message id


# --- Example usage ---
if __name__ == "__main__":
    conn = sqlite3.connect(":memory:")  # in-memory DB, replace with "mydb.sqlite" to persist
    init_db(conn)

    conv_id = create_conversation(conn)
    print("New conversation ID:", conv_id)

    add_message(conn, conv_id, "user", "Hello!")
    add_message(conn, conv_id, "assistant", "Hi, how can I help?")
    
    # Show messages
    for row in conn.execute("SELECT * FROM messages WHERE conversation_id = ?", (conv_id,)):
        print(row)
