from backend.log import Log
from site_packages.database import Database
from datetime import datetime, timedelta
from site_packages.encryption import RSA
from site_packages.password import PasswordManager
from backend.response import CustomResponse


def get_user(event):
    """
    Fetch a user from the database based on the provided user ID or username
    :param event: which is the event dict structured as follows:
        body: {
            userId: which is the ID of the user
            username: which is the username of the user
        }
    :return:
    """
    invoker_username = event.get("body", {}).get("invokerUsername")

    # check for body in the event
    if not event.get("body"):
        return {"statusCode": 400, "message": "No body provided."}
    body = event["body"]

    rsa = RSA()
    if not event.get("userId") and not event.get("username"):
        return {"statusCode": 400, "Message": "No username given"}

    query = """
            SELECT user.id, user.username, user.created_on, ur.name, ur.id, user.password
            FROM user 
            INNER JOIN user_role ur on ur.id = user.user_role_id
            """
    query_params = {}

    if body.get("userId"):
        query += "WHERE user.id = :user_id"
        query_params = {"user_id": event["userId"]}

    if body.get("username"):
        query += "WHERE user.username = :username"
        encrypted_username = rsa.encrypt(event["userName"])
        query_params = {"username": encrypted_username}

    with Database() as (_, cur):
        try:
            cur.execute(
                query,
                query_params,
            )
        except:
            return {"statusCode": 500, "message": "Could not fetch user"}

        user = cur.fetchone()
        if not user:
            return {"statusCode": 404, "message": "User not found"}

        user_id, encrypted_username, created_on, user_role_name, user_role_id, user_hashed_password = user
        decrypted_username = rsa.decrypt(eval(encrypted_username))
        decrypted_user = ({
            "id": user_id,
            "username": decrypted_username,
            "created_on": created_on,
            "user_role_name": user_role_name,
            "user_role_id": user_role_id,
            "hashed_password": user_hashed_password
        })

    return CustomResponse(200, invoker_username, "Successfully retrieved user", "Successfully retrieved user", False, decrypted_user)


def get_users(event):
    """
    Fetch all users from the database and return them in a list
    :param event: which is the event dict structured as follows:
        header: {
            userRoleId: which is the role ID of the user
        }
    :return: dict with status code, message, and users
    """
    invoker_username = event.get("body", {}).get("invokerUsername")

    rsa = RSA()

    query = """
                SELECT user.id, user.username, user.created_on, ur.name, ur.id
                FROM user
                INNER JOIN user_role ur on ur.id = user.user_role_id
            """
    query_dict = {}

    if "userRoleId" in event.get("header", {}):
        query += "WHERE user.user_role_id = :userRoleId"
        query_dict = {"userRoleId": event["header"]["userRoleId"]}


    with Database() as (_, cur):
        try:
            cur.execute(
                query,
                query_dict
            )
        except:
            return CustomResponse(500, invoker_username, "Could not fetch users", "Could not fetch users", False)

        users = cur.fetchall()


        decrypted_users = []
        for user in users:
            user_id, encrypted_username, created_on, user_role_name, user_role_id = user
            decrypted_username = rsa.decrypt(encrypted_username)
            decrypted_users.append({
                "id": user_id,
                "username": decrypted_username,
                "created_on": created_on,
                "user_role_name": user_role_name,
                "user_role_id": user_role_id
            })

    Log().log_activity(invoker_username, 'Get users', 'Successfully retrieved users', False)
    return {"statusCode": 200, "message": "Successfully retrieved users", "users": decrypted_users}


def add_user(event):
    """
    Add a new user to the database with the provided username, password, and role ID
    :param event: which is the event dict structured as follows:
        body: {
            username: which is the username of the user
            password: which is the password of the user
            userRoleId: which is the role ID of the user
        }
    :return: dict with status code, message, and additional information
    """
    invoker_username = event.get("body", {}).get("invokerUsername")

    rsa = RSA()
    if not event.get("body"):
        return CustomResponse(400, invoker_username, "No body provided", "tried to add user without a body", False)
    body = event["body"]

    if not body.get("username"):
        return CustomResponse(400, invoker_username, "Username is required", f"tried to add {body.get('username')}", False)
    encrypted_username = rsa.encrypt(body["username"])


    if not body.get("password"):
        return CustomResponse(400, invoker_username, "Password is required", f"tried to add {body['username']}", False)
    hashed_password = PasswordManager().hash_password(body["password"])


    if not body.get("userRoleId"):
        return CustomResponse(400, invoker_username, "Role is required", f"tried to add {body['username']}", False)
    user_role_id = body.get("userRoleId")

    with Database() as (_, cur):
        try:
            if username_exists(encrypted_username, cur):
                return CustomResponse(409, invoker_username, "Username already exists", f"tried to add {body['username']}", False)



            # Insert the user into the user table
            cur.execute(
                """
                INSERT INTO user (username, password, password_expiry, created_on, user_role_id) 
                VALUES (:username, :password, :password_expiry, :created_on, :user_role_id)
                """,
                {
                    "username": encrypted_username,
                    "password": hashed_password,
                    "password_expiry": datetime.now().replace(microsecond=0) + timedelta(days=365),
                    "created_on": datetime.now().replace(microsecond=0),
                    "user_role_id": user_role_id
                }
            )
        except Exception as e:
            return CustomResponse(500, invoker_username, f"{e} Could not add user", f"tried to add {body['username']}", False)

    return CustomResponse(200, invoker_username, "Added user successfully", f"Added {body['username']}", False)


def edit_user(event):
    """
    Edit a user's username, password, or role based on the provided user ID
    :param event: which is the event dict structured as follows:
        body: {
            userId: which is the ID of the user to be edited
            username: which is the new username
            password: which is the new password
            user_role_id: which is the new role ID
        }
    :return: dict with status code, message, and additional information
    """
    invoker_username = event.get("body", {}).get("invokerUsername")
    print("invoker_username: ", invoker_username)

    rsa = RSA()
    if not event.get("body"):
        return {"statusCode": 400, "Message": "No body provided."}
    
    body = event["body"]

    # Initialize variables to hold encrypted username and hashed password
    encrypted_username = None
    hashed_password = None
    
    # Handle username
    if body.get("username"):
        encrypted_username = rsa.encrypt(body["username"])
    else:
        return {"statusCode": 400, "Message": "Username is required."}
    
    # Handle password
    if body.get("password"):
        hashed_password = PasswordManager().hash_password(body["password"])

    if not body.get("userId"):
        return CustomResponse(400, invoker_username, "No user ID provided", "No user ID provided", False)

    with Database() as (_, cur):
        try:
            if username_changed(encrypted_username, body.get("userId"), cur) and username_exists(encrypted_username, cur):
                return {"statusCode": 409, "message": "Username already exists"}

            # Update username if it's provided
            if encrypted_username:
                cur.execute(
                    """
                    UPDATE user 
                    SET username = :username
                    WHERE id = :user_id
                    """,
                    {
                        "username": encrypted_username,
                        "user_id": body["userId"],
                    },
                )

            # Update password if it's provided
            if hashed_password:
                cur.execute(
                    """
                    UPDATE user 
                    SET password = :password, password_expiry = :password_expiry
                    WHERE id = :user_id
                    """,
                    {
                        "password": hashed_password,
                        "password_expiry": datetime.now().replace(microsecond=0) + timedelta(days=365),
                        "user_id": body["userId"],
                    },
                )

            # Update user role if provided
            if 'user_role_id' in body:
                cur.execute(
                    """
                    UPDATE user 
                    SET user_role_id = :user_role_id
                    WHERE id = :user_id
                    """,
                    {
                        "user_role_id": body["user_role_id"],
                        "user_id": body["userId"],
                    },
                )
        except Exception as e:
            return CustomResponse(500, invoker_username, "Could not edit user", f"ERROR while updating user in database: {str(e)}", False)

    return CustomResponse(200, invoker_username, "Successfully edited user", f"Edited user with ID: {body['userId']}", False)


def delete_user(event):
    """
    Delete a user from the database based on the provided user ID
    :param event: which is the event dict structured as follows:
        body: {
            userId: which is the ID of the user to be deleted
        }
    :return: dict with status code, message, and additional information
    """
    if not event.get("body"):
        return {"statusCode": 400, "message": "No body provided."}
    
    body = event["body"]

    if not body.get("userId"):
        return {"statusCode": 400, "message": "No user ID provided."}
    
    user_id = body["userId"]

    with Database() as (_, cur):
        try:
            cur.execute(
                """
                DELETE FROM user
                WHERE id = :user_id
                """,
                {"user_id": user_id},
            )
            # Check if any row was deleted
            if cur.rowcount == 0:
                return CustomResponse(404, event.get("invokerUsername"), "Could not delete user", "User not found", False)

        except Exception as e:  # Capture the exception
            print(f"Error occurred during deletion: {str(e)}")  # Log the error for debugging
            return CustomResponse(500, event.get("body", {}).get("invokerUsername"), "Could not delete user", f"ERROR while deleting user in database: {str(e)}", False)

    return CustomResponse(200, event.get("body", {}).get("invokerUsername"), "Successfully deleted user", f"Deleted user with ID: {user_id}", False)


def username_exists(username, cur):
    """
    Check if a username already exists in the database
    :param username: which is the username to check
    :param cur: which is the cursor object
    :return: boolean indicating if the username exists
    """
    cur.execute(
        """
        SELECT 1 
        FROM user 
        WHERE username = :username
        """,
        {"username": username},
    )

    return cur.fetchone() is not None


def username_changed(username, user_id, cur):
    """
    Check if the username has changed for a user
    :param username: which is the new username
    :param user_id: which is the ID of the user
    :param cur: which is the cursor object
    :return: boolean indicating if the username has changed
    """
    cur.execute(
        """
        SELECT username 
        FROM user 
        WHERE id = :user_id
        """,
        {"user_id": user_id},
    )

    old_username = cur.fetchone()[0]

    return username != old_username
