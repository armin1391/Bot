# =========================================================
# 👋 سیستم خوش‌آمدگویی و خداحافظی
# =========================================================


# =========================================================
# 👤 گرفتن نام کاربر
# =========================================================

def get_user_name(user):

    if not user:
        return "کاربر"

    first_name = user.get(
        "first_name"
    )

    last_name = user.get(
        "last_name"
    )

    if first_name and last_name:

        return (
            f"{first_name} "
            f"{last_name}"
        )

    if first_name:

        return first_name

    if last_name:

        return last_name

    return "کاربر"


# =========================================================
# 👋 پیام خوش‌آمدگویی
# =========================================================

def send_welcome_message(
    message,
    send_message
):

    chat = message.get(
        "chat",
        {}
    )

    new_members = message.get(
        "new_chat_members",
        []
    )

    if not new_members:

        return False

    chat_id = chat.get(
        "id"
    )

    if chat_id is None:

        return False

    # =====================================================
    # 🏠 نام گروه
    # =====================================================

    group_name = (
        chat.get("title")
        or "گروه"
    )

    # =====================================================
    # 👥 ممکن است چند نفر همزمان عضو شوند
    # =====================================================

    for user in new_members:

        user_name = get_user_name(
            user
        )

        welcome_text = (

            f"👋 سلام {user_name} !\n"
            "\n"

            f"خیلی خوش اومدی به گروه "
            f"{group_name} ❤️\n"
            "\n"

            "💙 حضور تو باعث خوشحالی ماست!"
        )

        send_message(
            chat_id,
            welcome_text
        )

    return True


# =========================================================
# 👋 پیام خداحافظی
# =========================================================

def send_goodbye_message(
    message,
    send_message
):

    chat = message.get(
        "chat",
        {}
    )

    left_member = message.get(
        "left_chat_member"
    )

    if not left_member:

        return False

    chat_id = chat.get(
        "id"
    )

    if chat_id is None:

        return False

    # =====================================================
    # 👤 نام کاربری که خارج شده
    # =====================================================

    user_name = get_user_name(
        left_member
    )

    # =====================================================
    # 👋 متن خداحافظی
    # =====================================================

    goodbye_text = (

        f"👋 خداحافظ {user_name}!\n"
        "\n"

        "💙 امیدواریم دوباره برگردی."
    )

    send_message(
        chat_id,
        goodbye_text
    )

    return True


# =========================================================
# 🔄 پردازش ورود و خروج کاربران
# =========================================================

def handle_welcome(
    message,
    send_message
):

    # =====================================================
    # 👋 کاربر جدید
    # =====================================================

    if message.get(
        "new_chat_members"
    ):

        send_welcome_message(
            message,
            send_message
        )

        return True

    # =====================================================
    # 👋 کاربر خارج شده
    # =====================================================

    if message.get(
        "left_chat_member"
    ):

        send_goodbye_message(
            message,
            send_message
        )

        return True

    return False