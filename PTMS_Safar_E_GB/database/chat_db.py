import sqlite3
import os
import json
from datetime import datetime


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

DB_PATH = os.path.join(
    DATA_DIR,
    "travelmate.db"
)


# =========================================================
# CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            trip_info TEXT DEFAULT '{}',

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id INTEGER NOT NULL,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            created_at TEXT NOT NULL,

            FOREIGN KEY(chat_id)
                REFERENCES chats(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# CREATE CHAT
# =========================================================

def create_chat(
    title="New Chat",
    trip_info=None
):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now().isoformat()

    if trip_info is None:
        trip_info = {}

    cursor.execute(
        """
        INSERT INTO chats (
            title,
            trip_info,
            created_at,
            updated_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            title,
            json.dumps(trip_info),
            now,
            now
        )
    )

    chat_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return chat_id


# =========================================================
# UPDATE CHAT
# =========================================================

def update_chat(
    chat_id,
    title=None,
    trip_info=None
):

    connection = get_connection()

    cursor = connection.cursor()

    updates = []
    values = []

    if title is not None:

        updates.append(
            "title = ?"
        )

        values.append(title)

    if trip_info is not None:

        updates.append(
            "trip_info = ?"
        )

        values.append(
            json.dumps(trip_info)
        )

    updates.append(
        "updated_at = ?"
    )

    values.append(
        datetime.now().isoformat()
    )

    values.append(chat_id)

    query = f"""
        UPDATE chats

        SET {", ".join(updates)}

        WHERE id = ?
    """

    cursor.execute(
        query,
        values
    )

    connection.commit()

    connection.close()


# =========================================================
# ADD MESSAGE
# =========================================================

def add_message(
    chat_id,
    role,
    content
):

    connection = get_connection()

    cursor = connection.cursor()

    now = datetime.now().isoformat()

    cursor.execute(
        """
        INSERT INTO messages (
            chat_id,
            role,
            content,
            created_at
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            chat_id,
            role,
            content,
            now
        )
    )

    cursor.execute(
        """
        UPDATE chats

        SET updated_at = ?

        WHERE id = ?
        """,
        (
            now,
            chat_id
        )
    )

    connection.commit()

    connection.close()


# =========================================================
# GET ALL CHATS
# =========================================================

def get_all_chats():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            trip_info,
            created_at,
            updated_at

        FROM chats

        ORDER BY updated_at DESC
        """
    )

    chats = cursor.fetchall()

    connection.close()

    return chats


# =========================================================
# GET SINGLE CHAT
# =========================================================

def get_chat(
    chat_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            title,
            trip_info,
            created_at,
            updated_at

        FROM chats

        WHERE id = ?
        """,
        (
            chat_id,
        )
    )

    chat = cursor.fetchone()

    connection.close()

    return chat


# =========================================================
# GET CHAT MESSAGES
# =========================================================

def get_chat_messages(
    chat_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            role,
            content,
            created_at

        FROM messages

        WHERE chat_id = ?

        ORDER BY id ASC
        """,
        (
            chat_id,
        )
    )

    messages = cursor.fetchall()

    connection.close()

    return messages


# =========================================================
# DELETE CHAT
# =========================================================

def delete_chat(
    chat_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE chat_id = ?
        """,
        (
            chat_id,
        )
    )

    cursor.execute(
        """
        DELETE FROM chats
        WHERE id = ?
        """,
        (
            chat_id,
        )
    )

    connection.commit()

    connection.close()