from datetime import datetime, timedelta

from backend.log import Log
from backend.response import CustomResponse
from site_packages.database import Database
import secrets
import string

from site_packages.password import PasswordManager


def generate_temporary_password(length=12):
    """
    Generate a temporary password
    :param length: which is the length of the password
    :return: the temporary password
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    temporary_password = ''.join(secrets.choice(characters) for _ in range(length))
    return temporary_password


def reset_consultant_password_with_temporary_password(event):
    """
    Reset the password of a consultant with a temporary password
    :param event: which is the event dict structured as follows:
        body: {
            userId: which is the ID of the consultant
            invokerUsername: which is the username of the user who invoked the action
        }
    :return: the custom response dict with status code and message
    """
    if not event.get("body"):
        return {"statusCode": 400, "message": "No body provided."}
    body = event["body"]

    if not body.get("userId"):
        return {"statusCode": 400, "message": "No user given."}
    user_id = body["userId"]

    with Database() as (_, cur):
        try:
            # Generate a temporary password
            temporary_password = generate_temporary_password()
            hashed_password = PasswordManager().hash_password(temporary_password)

            cur.execute(
                """
                UPDATE user 
                SET password = :password, password_expiry = :password_expiry
                WHERE id = :user_id
                """,
                {
                    "password": hashed_password,
                    "password_expiry": datetime.now().replace(microsecond=0) + timedelta(days=1),
                    "user_id": user_id,
                },
            )
        except Exception as e:
            print("Error: ", e)
            return CustomResponse(500, body.get("invokerUsername"), "Could not reset password",
                                  f"ERROR while updating user in database: {str(e)}", False)

    Log().log_activity(body.get("invokerUsername"), "Reset consultant password",
                       f"{body.get('invokerUsername')} reset password with a temporary password", False)
    return {"statusCode": 200, "message": "Password reset successfully: " + temporary_password}