# =========================================================
# ضد عکس
# =========================================================


from database.database import get_group_setting


# =========================================================
# بررسی ادمین
# =========================================================

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


# =========================================================
# پردازش ضد عکس
# =========================================================

def handle_anti_photo(
    message,
    admins,
    delete_message
):

    chat = message.get(
        "chat",
        {}
    )

    chat_type = chat.get(
        "type"
    )


    # =====================================================
    # فقط گروه و سوپرگروه
    # =====================================================

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
    # بررسی فعال بودن ضد عکس
    # =====================================================

    if not get_group_setting(
        chat_id,
        "anti_photo"
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
    # تشخیص عکس
    # =====================================================

    photo = message.get(
        "photo"
    )


    if not photo:

        return False


    # =====================================================
    # دریافت شناسه پیام
    # =====================================================

    message_id = message.get(
        "message_id"
    )


    if message_id is None:

        return False


    # =====================================================
    # حذف عکس
    # =====================================================

    success = delete_message(
        chat_id,
        message_id
    )


    # =====================================================
    # پیام مدیریت شد
    # =====================================================

    if success:

        return True


    return False