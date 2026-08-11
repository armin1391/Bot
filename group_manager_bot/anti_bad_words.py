import time
import threading
import re

from database.database import (
    get_group_setting,
    add_user_warning,
    set_user_mute,
    is_user_muted
)


# ---------------------------------
# نوع اخطار ضد فحش
# ---------------------------------

WARNING_TYPE = "anti_bad_words"


# ---------------------------------
# قفل اخطار
# ---------------------------------

warning_lock = threading.Lock()


# ---------------------------------
# لیست کلمات ممنوع
# ---------------------------------

BAD_WORDS = {
    "کس",
    "کص",

    "کسکش",
    "کصکش",

    "کسنمک",
    "کصنمک",

    "کسننه",
    "کصننه",

    "کسننت",
    "کصننت",

    "مادر",
    "مادر خراب",
    "مادر جنده",

    "کسخارت",
    "کصخارت",

    "سکس خارت",
    "صکس خارت",

    "مادر سگ",

    "کس ننت",
    "کص ننت",

    "آبمو",
    "آبم",
    "آب",

    "چوچول",
    "کردمت",

    "سکس",
    "صکس",

    "مادرتو",
    "خارتو",
    "خواهرتو",

    "گاییدم",
    "گاییده",
    "گایید",

    "خارکسده",
    "خارکصده",

    "خار کسده",
    "خار کصده",

    "مامانت",

    "سکسننت",
    "صکسننت",

    "ننت",
}


# ---------------------------------
# آماده‌سازی کلمات
# ---------------------------------

def normalize_text(text):

    if not text:
        return ""

    text = text.strip().lower()

    # تبدیل فاصله‌های مختلف به فاصله معمولی
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ---------------------------------
# تشخیص فحش
# ---------------------------------

def contains_bad_word(text):

    text = normalize_text(text)

    if not text:
        return False

    # بررسی عبارت‌های چندکلمه‌ای و تک‌کلمه‌ای
    words = text.split(" ")

    for bad_word in BAD_WORDS:

        bad_word = normalize_text(
            bad_word
        )

        bad_words_parts = bad_word.split(" ")

        # عبارت چندکلمه‌ای
        if len(bad_words_parts) > 1:

            for i in range(
                len(words) - len(bad_words_parts) + 1
            ):

                section = words[
                    i:i + len(bad_words_parts)
                ]

                if section == bad_words_parts:

                    return True

        # کلمه کامل
        else:

            if bad_word in words:

                return True

    return False


# ---------------------------------
# پردازش ضد فحش
# ---------------------------------

def handle_anti_bad_words(
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


    # ---------------------------------
    # اگر ضد فحش خاموش است
    # ---------------------------------

    if not get_group_setting(
        chat_id,
        "anti_bad_words"
    ):
        return False


    # ---------------------------------
    # ادمین‌ها مستثنی هستند
    # ---------------------------------

    if is_admin(
        admins,
        user_id
    ):
        return False


    # ---------------------------------
    # فقط پیام متنی
    # ---------------------------------

    text = message.get(
        "text"
    )

    if not text:
        return False


    # ---------------------------------
    # بررسی فحش
    # ---------------------------------

    if not contains_bad_word(
        text
    ):
        return False


    # ---------------------------------
    # حذف پیام
    # ---------------------------------

    message_id = message.get(
        "message_id"
    )

    if message_id is not None:

        delete_message(
            chat_id,
            message_id
        )


    # ---------------------------------
    # ثبت اخطار
    # ---------------------------------

    with warning_lock:

        warning_count = add_user_warning(
            chat_id,
            user_id,
            WARNING_TYPE
        )


        # ---------------------------------
        # اخطار اول
        # ---------------------------------

        if warning_count == 1:

            send_message(
                chat_id,
                "⚠️ استفاده از کلمات نامناسب ممنوع است.\n"
                "این اولین اخطار ضد فحش شماست."
            )

            return True


        # ---------------------------------
        # اخطار دوم
        # ---------------------------------

        if warning_count == 2:

            mute_until = int(
                time.time()
            ) + (60 * 60)

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
                    "🔇 به دلیل تکرار استفاده از کلمات نامناسب، "
                    "شما به مدت ۱ ساعت سکوت شدید.\n"
                    "این اخطار دوم ضد فحش شماست."
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ اخطار دوم ثبت شد، "
                    "اما ربات نتوانست کاربر را سکوت کند."
                )

            return True


        # ---------------------------------
        # اخطار سوم
        # ---------------------------------

        if warning_count >= 3:

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
                    "🔇 به دلیل تکرار استفاده از کلمات نامناسب، "
                    "شما به صورت دائمی سکوت شدید.\n"
                    "برای حذف سکوت، از ادمین گروه بخواهید."
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ اخطار سوم ثبت شد، "
                    "اما ربات نتوانست کاربر را سکوت کند."
                )

            return True


    return False


# ---------------------------------
# بررسی ادمین بودن
# ---------------------------------

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