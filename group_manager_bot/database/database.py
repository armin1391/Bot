import sqlite3
import threading
import time


DATABASE_NAME = "bot.db"

_db_lock = threading.RLock()


# =========================================================
# 🔌 اتصال به دیتابیس
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_NAME,
        check_same_thread=False,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================================
# 🗄️ ساخت دیتابیس و جداول
# =========================================================

def init_database():

    with _db_lock:

        connection = get_connection()

        # =====================================================
        # 👤 کاربران
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (

                user_id INTEGER PRIMARY KEY,

                first_name TEXT,
                last_name TEXT,
                username TEXT,

                first_seen INTEGER NOT NULL,
                last_seen INTEGER NOT NULL
            )
        """)

        # =====================================================
        # 👥 گروه‌ها
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS groups (

                chat_id INTEGER PRIMARY KEY,

                title TEXT,

                activated INTEGER NOT NULL DEFAULT 0,

                bot_joined INTEGER NOT NULL DEFAULT 1,

                created_at INTEGER NOT NULL
            )
        """)

        # =====================================================
        # 🔄 سازگاری با دیتابیس‌های قدیمی
        # =====================================================

        columns = connection.execute("""
            PRAGMA table_info(groups)
        """).fetchall()

        column_names = {
            column["name"]
            for column in columns
        }

        if "bot_joined" not in column_names:

            connection.execute("""
                ALTER TABLE groups

                ADD COLUMN bot_joined
                INTEGER NOT NULL DEFAULT 1
            """)

        # =====================================================
        # ⚙️ تنظیمات گروه
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (

                chat_id INTEGER PRIMARY KEY,

                anti_spam INTEGER NOT NULL DEFAULT 0,
                anti_bad_words INTEGER NOT NULL DEFAULT 0,
                anti_link INTEGER NOT NULL DEFAULT 0,
                anti_forward INTEGER NOT NULL DEFAULT 0,
                anti_video INTEGER NOT NULL DEFAULT 0,
                anti_photo INTEGER NOT NULL DEFAULT 0,
                anti_voice INTEGER NOT NULL DEFAULT 0,

                FOREIGN KEY (chat_id)
                REFERENCES groups(chat_id)
                ON DELETE CASCADE
            )
        """)

        # =====================================================
        # 🚫 فیلتر کلمات گروه
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS filtered_words (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,

                word TEXT NOT NULL,

                response TEXT NOT NULL,

                created_at INTEGER NOT NULL,

                UNIQUE (
                    chat_id,
                    word
                ),

                FOREIGN KEY (chat_id)
                REFERENCES groups(chat_id)
                ON DELETE CASCADE
            )
        """)

        # =====================================================
        # 📢 کانال‌ها
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS channels (

                chat_id INTEGER PRIMARY KEY,

                title TEXT,
                username TEXT,

                created_at INTEGER NOT NULL
            )
        """)

        # =====================================================
        # ⚠️ اخطارها
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_warnings (

                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                warning_type TEXT NOT NULL,

                warning_count INTEGER NOT NULL DEFAULT 0,

                PRIMARY KEY (
                    chat_id,
                    user_id,
                    warning_type
                )
            )
        """)

        # =====================================================
        # 🔇 کاربران سکوت‌شده
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS muted_users (

                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                muted_until INTEGER,

                PRIMARY KEY (
                    chat_id,
                    user_id
                )
            )
        """)

        # =====================================================
        # 🔨 کاربران بن‌شده
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS banned_users (

                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                banned_at INTEGER NOT NULL,

                PRIMARY KEY (
                    chat_id,
                    user_id
                )
            )
        """)

        # =====================================================
        # 💬 پیام‌های گروه
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS group_messages (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                first_name TEXT,
                last_name TEXT,
                username TEXT,

                message_id INTEGER,

                created_at INTEGER NOT NULL,

                UNIQUE (
                    chat_id,
                    message_id
                )
            )
        """)

        # =====================================================
        # 👥 ورود و خروج اعضا
        # =====================================================

        connection.execute("""
            CREATE TABLE IF NOT EXISTS group_member_events (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,

                first_name TEXT,
                last_name TEXT,
                username TEXT,

                event_type TEXT NOT NULL,

                created_at INTEGER NOT NULL
            )
        """)

        # =====================================================
        # 📊 ایندکس پیام‌ها
        # =====================================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_group_messages_chat_time

            ON group_messages (
                chat_id,
                created_at
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_group_messages_chat_user

            ON group_messages (
                chat_id,
                user_id
            )
        """)

        # =====================================================
        # 📊 ایندکس ورود و خروج
        # =====================================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_member_events_chat_time

            ON group_member_events (
                chat_id,
                event_type,
                created_at
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_member_events_user

            ON group_member_events (
                chat_id,
                user_id,
                event_type
            )
        """)

        # =====================================================
        # 🚫 ایندکس فیلتر کلمات
        # =====================================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_filtered_words_chat

            ON filtered_words (
                chat_id
            )
        """)

        # =====================================================
        # 👥 ایندکس وضعیت گروه‌ها
        # =====================================================

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_groups_status

            ON groups (
                bot_joined,
                activated
            )
        """)

        connection.commit()

        connection.close()


# =========================================================
# 👤 کاربران
# =========================================================

def register_user(
    user_id,
    first_name=None,
    last_name=None,
    username=None
):

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO users (

                user_id,
                first_name,
                last_name,
                username,

                first_seen,
                last_seen
            )

            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                first_name = excluded.first_name,
                last_name = excluded.last_name,
                username = excluded.username,
                last_seen = excluded.last_seen
        """, (
            user_id,
            first_name,
            last_name,
            username,
            now,
            now
        ))

        connection.commit()

        connection.close()


def get_users_count():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count
            FROM users
        """).fetchone()

        connection.close()

        return result["count"]


# =========================================================
# 👥 گروه‌ها
# =========================================================

def group_exists(chat_id):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT 1

            FROM groups

            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        connection.close()

        return result is not None


# =========================================================
# 🟢 ثبت گروهی که ربات داخل آن عضو شده
# =========================================================

def register_group(
    chat_id,
    title=None,
    created_at=None
):

    if created_at is None:
        created_at = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO groups (

                chat_id,
                title,
                activated,
                bot_joined,
                created_at
            )

            VALUES (?, ?, 0, 1, ?)

            ON CONFLICT(chat_id)

            DO UPDATE SET

                title = excluded.title,

                bot_joined = 1
        """, (
            chat_id,
            title,
            created_at
        ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# 🔴 ثبت خروج ربات از گروه
# =========================================================

def mark_group_left(chat_id):

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            UPDATE groups

            SET

                bot_joined = 0,
                activated = 0

            WHERE chat_id = ?
        """, (
            chat_id,
        ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# 🟢 فعال کردن گروه
# =========================================================

def activate_group(
    chat_id,
    title,
    created_at=None
):

    if created_at is None:
        created_at = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO groups (

                chat_id,
                title,
                activated,
                bot_joined,
                created_at
            )

            VALUES (?, ?, 1, 1, ?)

            ON CONFLICT(chat_id)

            DO UPDATE SET

                title = excluded.title,

                activated = 1,

                bot_joined = 1
        """, (
            chat_id,
            title,
            created_at
        ))

        connection.execute("""
            INSERT OR IGNORE INTO group_settings (

                chat_id
            )

            VALUES (?)
        """, (
            chat_id,
        ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# 🔴 غیرفعال کردن گروه
# =========================================================

def deactivate_group(chat_id):

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            UPDATE groups

            SET activated = 0

            WHERE chat_id = ?
        """, (
            chat_id,
        ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# ❓ آیا گروه فعال است؟
# =========================================================

def is_group_activated(chat_id):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT activated

            FROM groups

            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        connection.close()

        if not result:
            return False

        return result["activated"] == 1


# =========================================================
# ❓ آیا ربات داخل گروه است؟
# =========================================================

def is_bot_in_group(chat_id):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT bot_joined

            FROM groups

            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        connection.close()

        if not result:
            return False

        return result["bot_joined"] == 1


# =========================================================
# 📊 تعداد گروه‌های فعال
# =========================================================

def get_groups_count():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM groups

            WHERE bot_joined = 1

            AND activated = 1
        """).fetchone()

        connection.close()

        return result["count"]


def get_active_groups_count():

    return get_groups_count()


# =========================================================
# 📊 تعداد کل گروه‌هایی که ربات داخل آنهاست
# =========================================================

def get_bot_groups_count():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM groups

            WHERE bot_joined = 1
        """).fetchone()

        connection.close()

        return result["count"]


# =========================================================
# 📊 تعداد گروه‌هایی که ربات عضو است ولی فعال نیست
# =========================================================

def get_inactive_groups_count():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM groups

            WHERE bot_joined = 1

            AND activated = 0
        """).fetchone()

        connection.close()

        return result["count"]


# =========================================================
# 📋 لیست تمام گروه‌هایی که ربات داخل آنهاست
# =========================================================

def get_bot_groups():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT

                chat_id,
                title,
                activated,
                bot_joined,
                created_at

            FROM groups

            WHERE bot_joined = 1

            ORDER BY created_at DESC
        """).fetchall()

        connection.close()

    return result


# =========================================================
# 📋 لیست گروه‌های فعال
# =========================================================

def get_active_groups():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT

                chat_id,
                title,
                activated,
                bot_joined,
                created_at

            FROM groups

            WHERE bot_joined = 1

            AND activated = 1

            ORDER BY created_at DESC
        """).fetchall()

        connection.close()

    return result


# =========================================================
# 📋 لیست گروه‌های غیرفعال
# =========================================================

def get_inactive_groups():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT

                chat_id,
                title,
                activated,
                bot_joined,
                created_at

            FROM groups

            WHERE bot_joined = 1

            AND activated = 0

            ORDER BY created_at DESC
        """).fetchall()

        connection.close()

    return result


# =========================================================
# 🚫 فیلتر کلمات
# =========================================================

def add_filtered_word(
    chat_id,
    word,
    response
):

    if not word:
        return False

    if not response:
        return False

    word = word.strip()
    response = response.strip()

    if not word or not response:
        return False

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO filtered_words (

                chat_id,
                word,
                response,
                created_at
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(
                chat_id,
                word
            )

            DO UPDATE SET

                response = excluded.response
        """, (
            chat_id,
            word,
            response,
            now
        ))

        connection.commit()

        connection.close()

    return True


def remove_filtered_word(
    chat_id,
    word
):

    if not word:
        return False

    word = word.strip()

    with _db_lock:

        connection = get_connection()

        cursor = connection.execute("""
            DELETE FROM filtered_words

            WHERE chat_id = ?

            AND word = ?
        """, (
            chat_id,
            word
        ))

        connection.commit()

        connection.close()

    return cursor.rowcount > 0


def get_filtered_word(
    chat_id,
    word
):

    if not word:
        return None

    word = word.strip()

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT

                word,
                response

            FROM filtered_words

            WHERE chat_id = ?

            AND word = ?
        """, (
            chat_id,
            word
        )).fetchone()

        connection.close()

    if not result:
        return None

    return {
        "word": result["word"],
        "response": result["response"]
    }


def get_all_filtered_words(
    chat_id
):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT

                word,
                response

            FROM filtered_words

            WHERE chat_id = ?

            ORDER BY id ASC
        """, (
            chat_id,
        )).fetchall()

        connection.close()

    return result


def get_filtered_response(
    chat_id,
    word
):

    result = get_filtered_word(
        chat_id,
        word
    )

    if not result:
        return None

    return result["response"]


# =========================================================
# 📢 کانال‌ها
# =========================================================

def register_channel(
    chat_id,
    title=None,
    username=None
):

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO channels (

                chat_id,
                title,
                username,
                created_at
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(chat_id)

            DO UPDATE SET

                title = excluded.title,
                username = excluded.username
        """, (
            chat_id,
            title,
            username,
            now
        ))

        connection.commit()

        connection.close()


def get_channels_count():

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM channels
        """).fetchone()

        connection.close()

        return result["count"]


# =========================================================
# ⚙️ تنظیمات گروه
# =========================================================

ALLOWED_GROUP_SETTINGS = {

    "anti_spam",
    "anti_bad_words",
    "anti_link",
    "anti_forward",
    "anti_video",
    "anti_photo",
    "anti_voice"
}


def ensure_group_settings(
    connection,
    chat_id
):

    connection.execute("""
        INSERT OR IGNORE INTO group_settings (

            chat_id
        )

        VALUES (?)
    """, (
        chat_id,
    ))


def set_group_setting(
    chat_id,
    setting,
    value
):

    if setting not in ALLOWED_GROUP_SETTINGS:
        return False

    with _db_lock:

        connection = get_connection()

        ensure_group_settings(
            connection,
            chat_id
        )

        query = f"""
            UPDATE group_settings

            SET {setting} = ?

            WHERE chat_id = ?
        """

        connection.execute(
            query,
            (
                1 if value else 0,
                chat_id
            )
        )

        connection.commit()

        connection.close()

    return True


def get_group_setting(
    chat_id,
    setting
):

    if setting not in ALLOWED_GROUP_SETTINGS:
        return False

    with _db_lock:

        connection = get_connection()

        ensure_group_settings(
            connection,
            chat_id
        )

        result = connection.execute(
            f"""
            SELECT {setting}

            FROM group_settings

            WHERE chat_id = ?
            """,
            (
                chat_id,
            )
        ).fetchone()

        connection.close()

    if result is None:
        return False

    return result[setting] == 1


# =========================================================
# ⚠️ اخطارها
# =========================================================

ALLOWED_WARNING_TYPES = {

    "anti_spam",
    "anti_link",
    "anti_bad_words"
}


def get_user_warning(
    chat_id,
    user_id,
    warning_type="anti_spam"
):

    if warning_type not in ALLOWED_WARNING_TYPES:
        return 0

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT warning_count

            FROM user_warnings

            WHERE chat_id = ?
            AND user_id = ?
            AND warning_type = ?
        """, (
            chat_id,
            user_id,
            warning_type
        )).fetchone()

        connection.close()

    if not result:
        return 0

    return result["warning_count"]


def add_user_warning(
    chat_id,
    user_id,
    warning_type="anti_spam"
):

    if warning_type not in ALLOWED_WARNING_TYPES:
        return 0

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO user_warnings (

                chat_id,
                user_id,
                warning_type,
                warning_count
            )

            VALUES (?, ?, ?, 1)

            ON CONFLICT(
                chat_id,
                user_id,
                warning_type
            )

            DO UPDATE SET

                warning_count =
                user_warnings.warning_count + 1
        """, (
            chat_id,
            user_id,
            warning_type
        ))

        result = connection.execute("""
            SELECT warning_count

            FROM user_warnings

            WHERE chat_id = ?
            AND user_id = ?
            AND warning_type = ?
        """, (
            chat_id,
            user_id,
            warning_type
        )).fetchone()

        connection.commit()

        connection.close()

    return result["warning_count"]


def reset_user_warnings(
    chat_id,
    user_id,
    warning_type=None
):

    with _db_lock:

        connection = get_connection()

        if warning_type is None:

            connection.execute("""
                DELETE FROM user_warnings

                WHERE chat_id = ?
                AND user_id = ?
            """, (
                chat_id,
                user_id
            ))

        else:

            if warning_type not in ALLOWED_WARNING_TYPES:

                connection.close()

                return False

            connection.execute("""
                DELETE FROM user_warnings

                WHERE chat_id = ?
                AND user_id = ?
                AND warning_type = ?
            """, (
                chat_id,
                user_id,
                warning_type
            ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# 🔇 سکوت کاربران
# =========================================================

def set_user_mute(
    chat_id,
    user_id,
    muted_until
):

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO muted_users (

                chat_id,
                user_id,
                muted_until
            )

            VALUES (?, ?, ?)

            ON CONFLICT(
                chat_id,
                user_id
            )

            DO UPDATE SET

                muted_until =
                excluded.muted_until
        """, (
            chat_id,
            user_id,
            muted_until
        ))

        connection.commit()

        connection.close()

    return True


def get_user_mute(
    chat_id,
    user_id
):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT muted_until

            FROM muted_users

            WHERE chat_id = ?
            AND user_id = ?
        """, (
            chat_id,
            user_id
        )).fetchone()

        connection.close()

    if not result:
        return None

    return result["muted_until"]


def is_user_muted(
    chat_id,
    user_id
):

    muted_until = get_user_mute(
        chat_id,
        user_id
    )

    if muted_until is None:

        with _db_lock:

            connection = get_connection()

            result = connection.execute("""
                SELECT 1

                FROM muted_users

                WHERE chat_id = ?
                AND user_id = ?
            """, (
                chat_id,
                user_id
            )).fetchone()

            connection.close()

        return result is not None

    if muted_until <= int(time.time()):

        remove_user_mute(
            chat_id,
            user_id
        )

        return False

    return True


def remove_user_mute(
    chat_id,
    user_id
):

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            DELETE FROM muted_users

            WHERE chat_id = ?
            AND user_id = ?
        """, (
            chat_id,
            user_id
        ))

        connection.commit()

        connection.close()

    return True


def get_muted_users_count(chat_id):

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM muted_users

            WHERE chat_id = ?

            AND (
                muted_until IS NULL
                OR muted_until > ?
            )
        """, (
            chat_id,
            now
        )).fetchone()

        connection.close()

    return result["count"]


# =========================================================
# 🔨 بن کاربران
# =========================================================

def set_user_ban(
    chat_id,
    user_id
):

    banned_at = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO banned_users (

                chat_id,
                user_id,
                banned_at
            )

            VALUES (?, ?, ?)

            ON CONFLICT(
                chat_id,
                user_id
            )

            DO UPDATE SET

                banned_at =
                excluded.banned_at
        """, (
            chat_id,
            user_id,
            banned_at
        ))

        connection.commit()

        connection.close()

    return True


def is_user_banned(
    chat_id,
    user_id
):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT 1

            FROM banned_users

            WHERE chat_id = ?
            AND user_id = ?
        """, (
            chat_id,
            user_id
        )).fetchone()

        connection.close()

    return result is not None


def remove_user_ban(
    chat_id,
    user_id
):

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            DELETE FROM banned_users

            WHERE chat_id = ?
            AND user_id = ?
        """, (
            chat_id,
            user_id
        ))

        connection.commit()

        connection.close()

    return True


def get_banned_users_count(
    chat_id
):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM banned_users

            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        connection.close()

    return result["count"]


# =========================================================
# 💬 ثبت پیام گروه
# =========================================================

def record_group_message(
    chat_id,
    user_id,
    first_name=None,
    last_name=None,
    username=None,
    message_id=None
):

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        # =================================================
        # 👤 ثبت / بروزرسانی کاربر
        # =================================================

        connection.execute("""
            INSERT INTO users (

                user_id,
                first_name,
                last_name,
                username,
                first_seen,
                last_seen
            )

            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                first_name = excluded.first_name,
                last_name = excluded.last_name,
                username = excluded.username,
                last_seen = excluded.last_seen
        """, (
            user_id,
            first_name,
            last_name,
            username,
            now,
            now
        ))

        # =================================================
        # 🛡️ ثبت پیام
        # =================================================

        cursor = connection.execute("""
            INSERT OR IGNORE INTO group_messages (

                chat_id,
                user_id,
                first_name,
                last_name,
                username,
                message_id,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            user_id,
            first_name,
            last_name,
            username,
            message_id,
            now
        ))

        connection.commit()

        connection.close()

    return cursor.rowcount > 0


# =========================================================
# 👥 ثبت ورود / خروج اعضا
# =========================================================

def record_member_event(
    chat_id,
    user_id,
    event_type,
    first_name=None,
    last_name=None,
    username=None
):

    if event_type not in (
        "join",
        "leave"
    ):

        return False

    now = int(time.time())

    with _db_lock:

        connection = get_connection()

        connection.execute("""
            INSERT INTO users (

                user_id,
                first_name,
                last_name,
                username,
                first_seen,
                last_seen
            )

            VALUES (?, ?, ?, ?, ?, ?)

            ON CONFLICT(user_id)

            DO UPDATE SET

                first_name = excluded.first_name,
                last_name = excluded.last_name,
                username = excluded.username,
                last_seen = excluded.last_seen
        """, (
            user_id,
            first_name,
            last_name,
            username,
            now,
            now
        ))

        connection.execute("""
            INSERT INTO group_member_events (

                chat_id,
                user_id,
                first_name,
                last_name,
                username,
                event_type,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            user_id,
            first_name,
            last_name,
            username,
            event_type,
            now
        ))

        connection.commit()

        connection.close()

    return True


# =========================================================
# 🕛 شروع روز
# =========================================================

def get_start_of_day(timestamp):

    local_time = time.localtime(
        timestamp
    )

    return int(
        time.mktime((
            local_time.tm_year,
            local_time.tm_mon,
            local_time.tm_mday,
            0,
            0,
            0,
            0,
            0,
            -1
        ))
    )


# =========================================================
# 💬 تعداد کل پیام‌های گروه
# =========================================================

def get_group_messages_count(chat_id):

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM group_messages

            WHERE chat_id = ?
        """, (
            chat_id,
        )).fetchone()

        connection.close()

    return result["count"]


# =========================================================
# 📨 تعداد پیام‌های امروز
# =========================================================

def get_today_group_messages_count(chat_id):

    now = int(time.time())

    today_start = get_start_of_day(
        now
    )

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM group_messages

            WHERE chat_id = ?

            AND created_at >= ?

            AND created_at < ?
        """, (
            chat_id,
            today_start,
            now
        )).fetchone()

        connection.close()

    return result["count"]


# =========================================================
# 🆕 تعداد اعضای جدید
# =========================================================

def get_new_members_count(
    chat_id,
    start_time,
    end_time=None
):

    if end_time is None:
        end_time = int(time.time())

    with _db_lock:

        connection = get_connection()

        result = connection.execute("""
            SELECT COUNT(*) AS count

            FROM group_member_events

            WHERE chat_id = ?

            AND event_type = 'join'

            AND created_at >= ?

            AND created_at < ?
        """, (
            chat_id,
            start_time,
            end_time
        )).fetchone()

        connection.close()

    return result["count"]


def get_today_new_members_count(chat_id):

    now = int(time.time())

    start = get_start_of_day(
        now
    )

    return get_new_members_count(
        chat_id,
        start,
        now
    )


# =========================================================
# 🏆 کاربران پرپیام
# =========================================================

def get_top_group_message_users(
    chat_id,
    limit=3,
    start_time=None,
    end_time=None
):

    try:
        limit = int(limit)

    except (TypeError, ValueError):
        limit = 3

    limit = max(
        1,
        min(
            100,
            limit
        )
    )

    if end_time is None:
        end_time = int(time.time())

    with _db_lock:

        connection = get_connection()

        if start_time is None:

            result = connection.execute("""
                SELECT

                    user_id,

                    MAX(first_name)
                    AS first_name,

                    MAX(last_name)
                    AS last_name,

                    MAX(username)
                    AS username,

                    COUNT(*) AS message_count

                FROM group_messages

                WHERE chat_id = ?

                GROUP BY user_id

                ORDER BY message_count DESC

                LIMIT ?
            """, (
                chat_id,
                limit
            )).fetchall()

        else:

            result = connection.execute("""
                SELECT

                    user_id,

                    MAX(first_name)
                    AS first_name,

                    MAX(last_name)
                    AS last_name,

                    MAX(username)
                    AS username,

                    COUNT(*) AS message_count

                FROM group_messages

                WHERE chat_id = ?

                AND created_at >= ?

                AND created_at < ?

                GROUP BY user_id

                ORDER BY message_count DESC

                LIMIT ?
            """, (
                chat_id,
                start_time,
                end_time,
                limit
            )).fetchall()

        connection.close()

    return result


# =========================================================
# 🔥 سه کاربر پرپیام امروز
# =========================================================

def get_today_top_message_users(
    chat_id,
    limit=3
):

    now = int(time.time())

    start = get_start_of_day(
        now
    )

    return get_top_group_message_users(
        chat_id,
        limit,
        start,
        now
    )


# =========================================================
# 📈 رشد اعضای گروه
# =========================================================

def get_member_growth(
    chat_id,
    current_start,
    current_end,
    previous_start,
    previous_end
):

    current_count = get_new_members_count(
        chat_id,
        current_start,
        current_end
    )

    previous_count = get_new_members_count(
        chat_id,
        previous_start,
        previous_end
    )

    if previous_count == 0:

        if current_count > 0:
            percentage = 100.0
        else:
            percentage = 0.0

    else:

        percentage = (
            (
                current_count - previous_count
            )
            / previous_count
        ) * 100

    return {

        "current": current_count,

        "previous": previous_count,

        "percentage": round(
            percentage,
            2
        )
    }


# =========================================================
# 📊 آمار کامل گروه
# =========================================================

def get_group_statistics(chat_id):

    now = int(time.time())

    today_start = get_start_of_day(
        now
    )

    yesterday_start = (
        today_start
        - 24 * 60 * 60
    )

    week_start = (
        today_start
        - 7 * 24 * 60 * 60
    )

    previous_week_start = (
        week_start
        - 7 * 24 * 60 * 60
    )

    month_start = (
        today_start
        - 30 * 24 * 60 * 60
    )

    previous_month_start = (
        month_start
        - 30 * 24 * 60 * 60
    )

    return {

        "messages":
            get_group_messages_count(
                chat_id
            ),

        "today_messages":
            get_today_group_messages_count(
                chat_id
            ),

        "muted":
            get_muted_users_count(
                chat_id
            ),

        "banned":
            get_banned_users_count(
                chat_id
            ),

        "today_new_members":
            get_new_members_count(
                chat_id,
                today_start,
                now
            ),

        "day_growth":
            get_member_growth(
                chat_id,

                today_start,
                now,

                yesterday_start,
                today_start
            ),

        "week_growth":
            get_member_growth(
                chat_id,

                week_start,
                now,

                previous_week_start,
                week_start
            ),

        "month_growth":
            get_member_growth(
                chat_id,

                month_start,
                now,

                previous_month_start,
                month_start
            ),

        "top_users":
            get_top_group_message_users(
                chat_id,
                3
            ),

        "today_top_users":
            get_today_top_message_users(
                chat_id,
                3
            )
        }
