import time
import threading

from database.database import (
    get_group_setting,
    add_user_warning,
    set_user_mute
)


# =========================================================
# نوع اخطار
# =========================================================

WARNING_TYPE = "anti_forward"


# =========================================================
# قفل اخطار
# =========================================================

warning_lock = threading.Lock()


# =========================================================
# بررسی ادمین
# =========================================================

def is_admin(admins, user_id):

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


# =========================================================
# تشخیص فوروارد
# =========================================================

def is_forwarded_message(message):

    if not message:
        return False

    # -----------------------------------------
    # حالت‌های مختلف فوروارد
    # -----------------------------------------

    if message.get("forward_from"):
        return True

    if message.get("forward_from_chat"):
        return True

    if message.get("forward_sender_name"):
        return True

    if message.get("forward_origin"):
        return True

    return False


# =========================================================
# پردازش ضد فوروارد
# =========================================================

def handle_anti_forward(
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
    # بررسی فعال بودن ضد فوروارد
    # =====================================================

    if not get_group_setting(
        chat_id,
        "anti_forward"
    ):
        return False


    # =====================================================
    # ادمین‌ها مستثنی
    # =====================================================

    if is_admin(
        admins,
        user_id
    ):
        return False


    # =====================================================
    # تشخیص فوروارد
    # =====================================================

    if not is_forwarded_message(
        message
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
                "⚠️ ارسال پیام فورواردی در این گروه ممنوع است.\n"
                "این اولین اخطار ضد فوروارد شماست."
            )

            return True


        # =================================================
        # اخطار دوم
        # =================================================

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
                    "🔇 به دلیل ارسال دوباره پیام فورواردی، "
                    "شما به مدت ۱ ساعت سکوت شدید.\n"
                    "این اخطار دوم ضد فوروارد شماست."
                )

            else:

                send_message(
                    chat_id,
                    "⚠️ اخطار دوم ثبت شد، "
                    "اما ربات نتوانست کاربر را سکوت کند."
                )

            return True


        # =================================================
        # اخطار سوم
        # =================================================

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
                    "🔇 به دلیل تکرار ارسال پیام فورواردی، "
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