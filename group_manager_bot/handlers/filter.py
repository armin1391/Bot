import sqlite3
import threading


DATABASE_NAME = "bot.db"

_db_lock = threading.RLock()


def get_connection():
    connection = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# 🗄️ ساخت جدول فیلترها
# =========================================================

def init_filters():

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            CREATE TABLE IF NOT EXISTS word_filters (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                trigger_word TEXT NOT NULL,

                reply_text TEXT NOT NULL,

                UNIQUE (
                    chat_id,
                    trigger_word
                )
            )
        """)

        connection.commit()
        connection.close()


# =========================================================
# ➕ اضافه کردن فیلتر
# =========================================================

def add_filter(
    chat_id,
    trigger_word,
    reply_text
):

    trigger_word = trigger_word.strip()
    reply_text = reply_text.strip()

    if not trigger_word or not reply_text:
        return False

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO word_filters (
                chat_id,
                trigger_word,
                reply_text
            )

            VALUES (?, ?, ?)

            ON CONFLICT(
                chat_id,
                trigger_word
            )

            DO UPDATE SET
                reply_text = excluded.reply_text
        """, (
            chat_id,
            trigger_word,
            reply_text
        ))

        connection.commit()
        connection.close()

    return True


# =========================================================
# ❌ حذف فیلتر
# =========================================================

def delete_filter(
    chat_id,
    trigger_word
):

    trigger_word = trigger_word.strip()

    if not trigger_word:
        return False

    with _db_lock:

        connection = get_connection()

        cursor = connection.execute("""
            DELETE FROM word_filters

            WHERE chat_id = ?
            AND trigger_word = ?
        """, (
            chat_id,
            trigger_word
        ))

        connection.commit()
        connection.close()

    return cursor.rowcount > 0


# =========================================================
# 🔎 پیدا کردن پاسخ فیلتر
# =========================================================

def get_filter_reply(
    chat_id,
    trigger_word
):

    trigger_word = trigger_word.strip()

    if not trigger_word:
        return None

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT reply_text

            FROM word_filters

            WHERE chat_id = ?
            AND trigger_word = ?
        """, (
            chat_id,
            trigger_word
        )).fetchone()

        connection.close()

    if result is None:
        return None

    return result["reply_text"]


# =========================================================
# 📋 دریافت تمام فیلترهای یک گروه
# =========================================================

def get_all_filters(
    chat_id
):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT
                trigger_word,
                reply_text

            FROM word_filters

            WHERE chat_id = ?

            ORDER BY id ASC
        """, (
            chat_id,
        )).fetchall()

        connection.close()

    return result