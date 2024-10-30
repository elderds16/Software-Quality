from site_packages.encryption import RSA
from site_packages.database import Database


def authorize_user(token: str, permission_id: str) -> bool:
    """
    Authorize a user based on the session token and permission ID provided
    :param token: which is the session token
    :param permission_id: which is the permission ID
    :return:
    """
    encrypted_token = RSA().encrypt(token)

    with Database() as (_, cur):
        # Get the user's role based on the session token
        cur.execute(
            """
                SELECT u.user_role_id
                FROM session
                INNER JOIN user u on session.user_id = u.id
                WHERE session_token=:token
            """,
            {
                "token": encrypted_token
            }
        )

        user_role_id = cur.fetchone()

        # Check if the user exists and has a role
        if not user_role_id:
            return False
        user_role_id = user_role_id[0]

        # Check if the user has the required permission
        cur.execute(
            """
                SELECT p.name, u.username
                FROM user_role ur
                INNER JOIN user_role_has_permission urhp on ur.id = urhp.user_role_id
                INNER JOIN permission p on p.id = urhp.permission_id
                INNER JOIN user u on u.user_role_id = ur.id
                WHERE urhp.user_role_id=:role_id AND urhp.permission_id=:permission_id
            """,
            {
                "role_id": user_role_id,
                "permission_id": permission_id
            }
        )

        fetch = cur.fetchone()

        # Check if the user has the required permission
        if not fetch:
            return False, None

        # Return the function name and the username
        function_name = fetch[0]
        username = fetch[1]
        decrypt_username = RSA().decrypt(username)
        return function_name, decrypt_username
