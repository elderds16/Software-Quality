import uuid
from datetime import datetime, timedelta

from backend.log import Log
from backend.response import CustomResponse
from site_packages.password import PasswordManager
from site_packages.encryption import RSA
from site_packages.database import Database

login_attempts = 0  # Usually should be tracked by IP address, but since it is a console application, it is tracked by run time


def login(username: str, password: str) -> dict:
    """
    Log in a user with a username and password and return a session token if successful
    :param username: which is the username of the user
    :param password: which is the password of the user
    :return: the session token if successful
    """
    global login_attempts

    encrypted_username = RSA().encrypt(username)

    with Database() as (_, cur):
        # Retrieve the password and user role of the user
        cur.execute("SELECT id, password, user_role_id FROM user WHERE username=:username", {"username": encrypted_username})
        user = cur.fetchone()

        # Check if the user exists and password is correct
        if user and PasswordManager().verify_password(password, user[1]):
            # Generate session token
            token = generate_session_token()
            encrypted_token = RSA().encrypt(token)

            # Store the session
            cur.execute(
                """
                INSERT INTO session (user_id, session_token, created_at, expires_at) 
                VALUES (:user_id, :token, :created_at, :expires_at)
                """,
                {
                    "user_id": user[0],
                    "token": encrypted_token,
                    "created_at": datetime.now().replace(microsecond=0),
                    "expires_at": datetime.now().replace(microsecond=0) + timedelta(days=1)
                }
            )

            # Retrieve the user permissions
            cur.execute(
                """
                SELECT p.id
                FROM user_role_has_permission urhp
                INNER JOIN permission p on urhp.permission_id = p.id
                WHERE urhp.user_role_id = :role_id
                """,
                {"role_id": user[2]}
            )

            permissions = [row[0] for row in cur.fetchall()]

            login_attempts = 0  # Reset login attempts
            response = {"statusCode": 200, "statusMessage": "Successfully logged in", "token": token, "permissions": permissions}  # Return session token to the user
            if is_password_almost_expired(encrypted_username, cur):
                response["passwordAlmostExpired"] = True

            return response
        else:
            # increment login attempts
            login_attempts += 1

            if login_attempts == 3 or login_attempts == 4:
                # In real life user should be notified through mail or sms
                Log().log_activity('...', f'Failed user login: {username}', f"Too many login attempts: {'Attempt: ', login_attempts}", suspicious=True)
                return {"statusCode": 401, "statusMessage": "Too many login attempts, Please try again later"}  # Return error message if login fails

            if login_attempts > 5:
                Log().log_activity('...', f'Failed user login: {username}', f"Too many login attempts: {'Attempt: ', login_attempts}", suspicious=True)
                return {"statusCode": 401, "statusMessage": "Too many login attempts, Temporary locked"} # Return error message if login fails

            Log().log_activity('...', f'Failed user login: {username}', 'Incorrect username or password', suspicious=False)
            return {"statusCode": 401, "statusMessage": "Incorrect username or password"}  # Return error message if login fails


def generate_session_token() -> str:
    """
    Generate a session token for the user
    :return: the session token
    """
    return str(uuid.uuid4())  # Generates a random unique identifier (token)


def logout(token: str, username) -> str:
    """
    Log out a user with a session token
    :param token: which is the session token
    :return: the response message
    """
    encrypted_token = RSA().encrypt(token)

    with Database() as (_, cur):
        cur.execute("DELETE FROM session WHERE session_token = :token", {"token": encrypted_token})

    if cur.rowcount == 0:
        return CustomResponse(400, username, "Failed to log out", "User not found", False)
    else:
        return CustomResponse(200, username, "Successfully logged out", "User logged out successfully", False)


def is_password_almost_expired(encrypted_username: str, cur: object) -> bool:
    """
    Check if the password of the user is almost expired (less than 7 days)
    :param encrypted_username: which is the encrypted username of the user
    :param cur: which is the database cursor
    :return: True if password is almost expired, False otherwise
    """

    cur.execute("""SELECT password_expiry FROM user
                WHERE username = :username""", {"username": encrypted_username})

    password_expiry_str = cur.fetchone()[0]

    # Convert string to datetime
    password_expiry = datetime.strptime(password_expiry_str, '%Y-%m-%d %H:%M:%S')

    # Now you can safely subtract
    if password_expiry - datetime.now().replace(microsecond=0) < timedelta(days=7):
        return True
    else:
        return False
