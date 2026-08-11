# =========================================================
# ضد فیلم
# =========================================================

from database.database import get_group_setting


# =========================================================
# بررسی ادمین
# =========================================================

def is_admin(admins, user_id):

    if not admins:
        return False

    if not admins.get("ok"):
        return False

    for admin in admins.get("result", []):

        user = admin.get("user", {})

        if user.get("id") == user_id:

            return admin.get("status") in (
                "administrator",
                "creator"
            )

    return False


# =========================================================
# پردازش ضد فیلم
# =========================================================

def handle_anti_video(
    message,
    admins,
    delete_message
):

    chat = message.get("chat", {})

    chat_type = chat.get("type")

    # فقط گروه و سوپرگروه
    if chat_type not in (
        "group",
        "supergroup"
    ):
        return False


    chat_id = chat.get("id")

    user = message.get("from", {})

    user_id = user.get("id")


    if not user_id:
        return False


    # =====================================================
    # اگر ضد فیلم خاموش است
    # =====================================================

    if not get_group_setting(
        chat_id,
        "anti_video"
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
    # تشخیص فیلم
    # =====================================================

    video = message.get("video")

    if not video:
        return False


    # =====================================================
    # حذف فیلم
    # =====================================================

    message_id = message.get("message_id")

    if message_id is None:
        return False


    success = delete_message(
        chat_id,
        message_id
    )


    if success:
        print(
            f"🎬 [ANTI-VIDEO] "
            f"Video deleted | "
            f"chat_id={chat_id} "
            f"user_id={user_id}"
        )

        return True


    print(
        f"❌ [ANTI-VIDEO] "
        f"Failed to delete video | "
        f"chat_id={chat_id} "
        f"user_id={user_id}"
    )

    return False