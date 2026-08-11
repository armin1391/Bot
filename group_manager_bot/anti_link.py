import time
import threading
import re

from database.database import (
    get_group_setting,
    get_user_warning,
    add_user_warning,
    set_user_mute,
    is_user_muted
)


# =========================================================
# نوع اخطار ضد لینک
# =========================================================

WARNING_TYPE = "anti_link"


# =========================================================
# قفل اخطار
# =========================================================

warning_lock = threading.Lock()


# =========================================================
# الگوهای تشخیص لینک و آیدی
# =========================================================

LINK_PATTERNS = [

    # HTTP / HTTPS
    re.compile(
        r"https?://[^\s]+",
        re.IGNORECASE
    ),

    # WWW
    re.compile(
        r"\bwww\.[^\s]+",
        re.IGNORECASE
    ),

    # دامنه بدون http
    re.compile(
        r"(?<![@\w-])"
        r"(?:[a-zA-Z0-9-]+\.)+"
        r"[a-zA-Z]{2,}"
        r"(?:/[^\s]*)?",
        re.IGNORECASE
    ),

    # آیدی با @
    re.compile(
        r"(?<!\w)@[a-zA-Z0-9_]{2,}",
        re.IGNORECASE
    )
]


# =========================================================
# تشخیص لینک
# =========================================================

def contains_link(text):

    if not text:
        return False

    for pattern in LINK_PATTERNS:

        if pattern.search(text):
            return True

    return False


# =========================================================
# پردازش ضد لینک
# =========================================================

def handle_anti_link(
    message,
    admins,
    send_message,
    delete_message,
    restrict_user
):

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )

    # فقط گروه و سوپرگروه
    if chat_type not in (
        "group",
        "supergroup"
    ):
        return False

    chat_id = chat.get(
        "id"
    )

    user = message.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    if not user_id:
        return False


    # =====================================================
    # اگر ضد لینک خاموش است
    # =====================================================

    if not get_group_setting(
        chat_id,
        "anti_link"
    ):
        return False


    # =====================================================
    # ادمین‌ها مستثنی هستند
    # =====================================================

    if is_admin(
        admins,
        user_id
    ):
        return False


    # =====================================================
    # متن پیام
    # =====================================================

    text = message.get(
        "text"
    )

    if not text:
        return False


    # =====================================================
    # بررسی لینک
    # =====================================================

    if not contains_link(
        text
    ):
        return False


    # =====================================================
    # حذف پیام
    # =====================================================

    message_id = message.get(
        "message_id"
    )

    if message_id is not None:

        delete_message(
            chat_id,
            message_id
        )


    # =====================================================
    # ثبت اخطار
    # =====================================================

    with warning_lock:

        current_warning = get_user_warning(
            chat_id,
            user_id,
            WARNING_TYPE
        )

        # حداکثر ۳ اخطار
        if current_warning >= 3:
            return True


        warning_count = add_user_warning(
            chat_id,
            user_id,
            WARNING_TYPE
        )


        # =================================================
        # اخطار اول
        # =================================================

        if warning_count == 1:

            send_message(
                chat_id,
                "⚠️ ارسال لینک ممنوع است.\n"
                "این اولین اخطار شماست."
            )

            return True


        # =================================================
        # اخطار دوم → یک ساعت سکوت
        # =================================================

        if warning_count == 2:

            mute_until = (
                int(time.time())
                + 60 * 60
            )

            success = restrict_user(
                chat_id,
                user_id,
                mute_until
            )

            if success:

                set_user_mute(
                    chat_id,
                    user_id,
                    mute_until
                )

                send_message(
                    chat_id,
                    "🔇 به دلیل ارسال مجدد لینک، "
                    "شما به مدت ۱ ساعت سکوت شدید.\n"
                    "این اخطار دوم شماست."
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ اخطار دوم ثبت شد، "
                    "اما ربات نتوانست شما را سکوت کند."
                )

            return True


        # =================================================
        # اخطار سوم → سکوت دائمی
        # =================================================

        if warning_count == 3:

            success = restrict_user(
                chat_id,
                user_id,
                None
            )

            if success:

                set_user_mute(
                    chat_id,
                    user_id,
                    None
                )

                send_message(
                    chat_id,
                    "🔇 به دلیل تکرار ارسال لینک، "
                    "شما به صورت دائمی سکوت شدید.\n"
                    "این اخطار سوم شماست."
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ اخطار سوم ثبت شد، "
                    "اما ربات نتوانست شما را سکوت کند."
                )

            return True


    return True


# =========================================================
# بررسی ادمین
# =========================================================

def is_admin(
    admins,
    user_id
):

    if not admins:
        return False

    if not admins.get(
        "ok"
    ):
        return False

    for admin in admins.get(
        "result",
        []
    ):

        user = admin.get(
            "user",
            {}
        )

        if user.get(
            "id"
        ) == user_id:

            return admin.get(
                "status"
            ) in (
                "administrator",
                "creator"
            )

    return False