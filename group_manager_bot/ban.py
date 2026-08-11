from database.database import set_user_ban, remove_user_ban


# ---------------------------------
# بررسی ادمین
# ---------------------------------

def is_admin(admins, user_id):

    if not admins or not admins.get("ok"):
        return False

    for admin in admins.get("result", []):

        user = admin.get("user", {})

        if user.get("id") == user_id:
            return admin.get("status") in (
                "administrator",
                "creator"
            )

    return False


# ---------------------------------
# بن کردن کاربر
# ---------------------------------

def ban_user(
    chat_id,
    user_id,
    ban_member
):

    success = ban_member(
        chat_id,
        user_id
    )

    if not success:
        return False

    set_user_ban(
        chat_id,
        user_id
    )

    return True


# ---------------------------------
# آن‌بن کردن کاربر
# ---------------------------------

def unban_user(
    chat_id,
    user_id,
    unban_member
):

    success = unban_member(
        chat_id,
        user_id
    )

    if not success:
        return False

    remove_user_ban(
        chat_id,
        user_id
    )

    return True