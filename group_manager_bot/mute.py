from database.database import (
    set_user_mute,
    remove_user_mute
)


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
# سکوت دائمی
# ---------------------------------

def mute_user(
    chat_id,
    user_id,
    restrict_user
):

    success = restrict_user(
        chat_id,
        user_id,
        None
    )

    if not success:
        return False

    set_user_mute(
        chat_id,
        user_id,
        None
    )

    return True


# ---------------------------------
# حذف سکوت
# ---------------------------------

def unmute_user(
    chat_id,
    user_id,
    unrestrict_user
):

    success = unrestrict_user(
        chat_id,
        user_id
    )

    if not success:
        return False

    remove_user_mute(
        chat_id,
        user_id
    )

    return True