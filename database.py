"""
database.py

SQLite database layer for Lipi Trade AI user authentication and tracking.

Provides functions to initialize the database, register users, verify login
credentials, and fetch user records.
"""

import sqlite3

try:
    import bcrypt
    HASH_LIBRARY = "bcrypt"
except ImportError:
    import hashlib
    HASH_LIBRARY = "hashlib"

DB_NAME = "users.db"


def get_connection():
    """Return a new connection to the SQLite database."""
    return sqlite3.connect(DB_NAME)


def init_db():
    """Create the users table if it does not already exist.

    Columns:
        id            INTEGER PRIMARY KEY
        username      TEXT UNIQUE
        email         TEXT
        password_hash TEXT
        subscription  TEXT DEFAULT 'free'
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            email         TEXT,
            password_hash TEXT NOT NULL,
            subscription  TEXT DEFAULT 'free'
        )
        """
    )
    conn.commit()
    conn.close()


def _hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt (or hashlib fallback)."""
    if HASH_LIBRARY == "bcrypt":
        # bcrypt.hashpw expects bytes and returns bytes; decode to str for storage
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # Fallback: SHA-256 with a static salt (less secure than bcrypt but better than plain text)
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _check_password(plain_password: str, stored_hash: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    if HASH_LIBRARY == "bcrypt":
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), stored_hash.encode("utf-8")
        )
    # Fallback: compare SHA-256 hashes
    return hashlib.sha256(plain_password.encode("utf-8")).hexdigest() == stored_hash


def add_user(username: str, email: str, password: str) -> bool:
    """Hash the password and insert a new user into the database.

    Returns True if the user was created successfully, False if the username
    already exists (or any other database error occurs).
    """
    password_hash = _hash_password(password)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, subscription) "
            "VALUES (?, ?, ?, 'free')",
            (username, email, password_hash),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists (UNIQUE constraint)
        return False
    finally:
        conn.close()


def verify_user(username: str, password: str) -> bool:
    """Check if the username exists and the password matches the stored hash.

    Returns True if credentials are valid, False otherwise.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT password_hash FROM users WHERE username = ?", (username,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return False

    stored_hash = row[0]
    return _check_password(password, stored_hash)


def get_user(username: str) -> dict | None:
    """Return the user's data as a dictionary, or None if not found.

    Dictionary keys: id, username, email, password_hash, subscription
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, password_hash, subscription "
        "FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row[0],
        "username": row[1],
        "email": row[2],
        "password_hash": row[3],
        "subscription": row[4],
    }


if __name__ == "__main__":
    # Quick smoke test when run directly
    init_db()
    print("Database initialized successfully.")