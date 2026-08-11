import time
import threading
from collections import defaultdict, deque

from database.database import (
    get_group_setting,
    get_user_warning,
    add_user_warning,
    set_user_mute,
    is_user_muted
)


# ---------------------------------
# تنظیمات ضد اسپم
# ---------------------------------

SPAM_MESSAGE_LIMIT = 7
SPAM_TIME_WINDOW = 10

WARNING_TYPE = "anti_spam"


# ---------------------------------
# حافظه موقت پیام‌ها
#
# برای هر گروه + کاربر جداست
# ---------------------------------

message_times = defaultdict(deque)


# ---------------------------------
# قفل پردازش اخطار
#
# جلوگیری از ثبت چند اخطار همزمان
# توسط Workerهای مختلف
# ---------------------------------

warning_lock = threading.Lock()


# ---------------------------------
# پاکسازی زمان‌های قدیمی
# ---------------------------------

def cleanup_old_messages(times, now):

    while times and now - times[0] > SPAM_TIME_WINDOW:
        times.popleft()


# ---------------------------------
# بررسی اسپم
# ---------------------------------

def is_spam(chat_id, user_id):

    now = time.time()

    key = (
        chat_id,
        user_id
    )

    times = message_times[key]

    cleanup_old_messages(
        times,
        now
    )

    times.append(now)

    return len(times) >= SPAM_MESSAGE_LIMIT


# ---------------------------------
# پردازش ضد اسپم
# ---------------------------------

def handle_anti_spam(
    message,
    admins,
    send_message,
    restrict_user
):

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get("type")

    # فقط گروه و سوپرگروه
    if chat_type not in (
        "group",
        "supergroup"
    ):
        return False

    chat_id = chat.get("id")

    user = message.get(
        "from",
        {}
    )

    user_id = user.get("id")

    if not user_id:
        return False

    # ---------------------------------
    # اگر ضد اسپم خاموش است
    # ---------------------------------

    if not get_group_setting(
        chat_id,
        "anti_spam"
    ):
        return False

    # ---------------------------------
    # ادمین‌ها و مالک مستثنی هستند
    # ---------------------------------

    if is_admin(
        admins,
        user_id
    ):
        return False

    # ---------------------------------
    # قفل پردازش
    #
    # مهم:
    # چند Worker نمی‌توانند همزمان
    # برای یک کاربر اخطار ثبت کنند.
    # ---------------------------------

    with warning_lock:

        # ---------------------------------
        # اگر کاربر از قبل سکوت است
        #
        # دیگر اخطار جدید نگیرد
        # ---------------------------------

        if is_user_muted(
            chat_id,
            user_id
        ):
            return True

        # ---------------------------------
        # بررسی اسپم
        # ---------------------------------

        if not is_spam(
            chat_id,
            user_id
        ):
            return False

        # ---------------------------------
        # ثبت اخطار
        # ---------------------------------

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
                "⚠️ لطفاً اسپم نکنید.\n"
                "این اولین اخطار شماست."
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

                # ذخیره سکوت در دیتابیس
                set_user_mute(
                    chat_id,
                    user_id,
                    mute_until
                )

                send_message(
                    chat_id,
                    "🔇 به دلیل تکرار اسپم، "
                    "شما به مدت ۱ ساعت سکوت شدید.\n"
                    "این اخطار دوم شماست."
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

            # ---------------------------------
            # سکوت دائمی
            # ---------------------------------

            success = restrict_user(
                chat_id,
                user_id,
                None
            )

            if success:

                # None = سکوت دائمی
                set_user_mute(
                    chat_id,
                    user_id,
                    None
                )

                send_message(
                    chat_id,
                    "🔇 به دلیل تکرار اسپم، "
                    "شما به صورت دائمی سکوت شدید.\n"
                    "برای حذف سکوت، از ادمین گروه بخواهید."
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

    if not admins.get("ok"):
        return False

    for admin in admins.get(
        "result",
        []
    ):

        user = admin.get(
            "user",
            {}
        )

        if user.get("id") == user_id:

            return admin.get(
                "status"
            ) in (
                "administrator",
                "creator"
            )

    return False