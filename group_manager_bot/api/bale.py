import requests

from config import BASE_URL


# =========================================================
# 🔌 درخواست اصلی API
# =========================================================

def api_request(
    method,
    data=None,
    timeout=10
):

    url = f"{BASE_URL}/{method}"

    try:

        response = requests.post(
            url,
            json=data or {},
            timeout=timeout
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        print(
            f"[API ERROR] {method}: {e}"
        )

        return None


# =========================================================
# 🏘️ دریافت اطلاعات گروه / چت
# =========================================================

def get_chat(
    chat_id
):

    return api_request(
        "getChat",
        {
            "chat_id": chat_id
        }
    )


# =========================================================
# 👑 دریافت ادمین‌های گروه
# =========================================================

def get_chat_administrators(
    chat_id
):

    return api_request(
        "getChatAdministrators",
        {
            "chat_id": chat_id
        }
    )


# =========================================================
# 📤 ارسال پیام
# =========================================================

def send_message(
    chat_id,
    text,
    components=None
):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if components is not None:

        data["reply_markup"] = components

    return api_request(
        "sendMessage",
        data
    )

    # -----------------------------------------------------
    # اگر دکمه وجود داشته باشد
    # -----------------------------------------------------

    if components is not None:

        data["components"] = components

    return api_request(
        "sendMessage",
        data
    )


# =========================================================
# 🔇 سکوت کردن کاربر
# =========================================================

def restrict_user(
    chat_id,
    user_id,
    until_date=None
):

    data = {
        "chat_id": chat_id,
        "user_id": user_id,

        "permissions": {
            "can_send_messages": False,
            "can_send_audios": False,
            "can_send_documents": False,
            "can_send_photos": False,
            "can_send_videos": False,
            "can_send_video_notes": False,
            "can_send_voice_notes": False,
            "can_send_polls": False,
            "can_send_other_messages": False,
            "can_add_web_page_previews": False,
            "can_change_info": False,
            "can_invite_users": False,
            "can_pin_messages": False,
            "can_manage_topics": False
        }
    }

    # -----------------------------------------------------
    # ⏱️ اگر زمان داشته باشد = سکوت موقت
    # اگر زمان نداشته باشد = سکوت دائمی
    # -----------------------------------------------------

    if until_date is not None:

        data["until_date"] = until_date

    result = api_request(
        "restrictChatMember",
        data
    )

    if not result:

        return False

    return result.get(
        "ok",
        False
    )


# =========================================================
# 🔊 حذف سکوت کاربر
# =========================================================

def unrestrict_user(
    chat_id,
    user_id
):

    data = {
        "chat_id": chat_id,
        "user_id": user_id,

        "permissions": {
            "can_send_messages": True,
            "can_send_audios": True,
            "can_send_documents": True,
            "can_send_photos": True,
            "can_send_videos": True,
            "can_send_video_notes": True,
            "can_send_voice_notes": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,

            # -------------------------------------------------
            # این‌ها دسترسی مدیریتی هستند
            # -------------------------------------------------

            "can_change_info": False,
            "can_invite_users": True,
            "can_pin_messages": False,
            "can_manage_topics": False
        }
    }

    result = api_request(
        "restrictChatMember",
        data
    )

    if not result:

        return False

    return result.get(
        "ok",
        False
    )


# =========================================================
# 🔨 بن کردن کاربر
# =========================================================

def ban_member(
    chat_id,
    user_id
):

    result = api_request(
        "banChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    return bool(
        result and result.get(
            "ok"
        )
    )


# =========================================================
# 🔓 آن‌بن کردن کاربر
# =========================================================

def unban_member(
    chat_id,
    user_id
):

    result = api_request(
        "unbanChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )

    return bool(
        result and result.get(
            "ok"
        )
    )


# =========================================================
# 🗑️ حذف پیام
# =========================================================

def delete_message(
    chat_id,
    message_id
):

    result = api_request(
        "deleteMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )

    if not result:

        return False

    return result.get(
        "ok",
        False
    )
