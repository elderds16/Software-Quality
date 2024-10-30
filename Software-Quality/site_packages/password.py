import bcrypt

from datetime import datetime, timedelta
from site_packages.database import Database
from site_packages.encryption import RSA


class PasswordManager:
    @staticmethod
    def hash_password(plain_password):
        """
        Hash the provided password using bcrypt and a salt
        :param plain_password: which is the password to hash
        :return:
        """
        if not plain_password:
            return None
        # Generate a salt and hash the
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
        return hashed_password

    @staticmethod
    def verify_password(plain_password, hashed_password):
        """
        Verify if the provided password matches the hashed password
        :param plain_password: which is the password to verify
        :param hashed_password: which is the hashed password to compare against
        :return:
        """
        # Verify if the provided password matches the hashed password
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)


def update_own_password(event):
    """
    Update the user's password with a new password
    :param event: which is the event dict structured as follows:
        header: {
            token: which is the session token
        }
        body: {
            password: which is the new password
        }
    :return:
    """
    if not event.get("body"):
        return {"statusCode": 400, "message": "No body provided."}
    body = event["body"]

    if not event.get("header"):
        return {"statusCode": 400, "message": "No header provided."}
    header = event["header"]

    if not header.get("token"):
        return {"statusCode": 400, "message": "No token provided."}
    token = header["token"]
    encrypted_token = RSA().encrypt(token)

    if not body.get("password"):
        return {"statusCode": 400, "message": "Password is required."}
    hashed_password = PasswordManager().hash_password(body["password"])

    with Database() as (_, cur):
        try:
            cur.execute(
                """
                SELECT user_id
                FROM session
                WHERE session_token = :session_token
                """,
                {"session_token": encrypted_token},
            )

            fetch = cur.fetchone()
            if not fetch:
                return {"statusCode": 401, "message": "Unauthorized"}
            user_id = fetch[0]

            cur.execute(
                """
                UPDATE user 
                SET password = :password, password_expiry = :password_expiry
                WHERE id = :user_id
                """,
                {
                    "password": hashed_password,
                    "password_expiry": datetime.now().replace(microsecond=0) + timedelta(days=365),
                    "user_id": user_id,
                },
            )
        except Exception as e:
            return {"statusCode": 500, "message": "Could not reset password"}

    return {"statusCode": 200, "message": "Successfully updated password"}
