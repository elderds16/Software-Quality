from backend.user import add_user, get_users, edit_user, delete_user
from backend.member import add_member, modify_member, delete_member, get_members
from backend.consultant import reset_consultant_password_with_temporary_password
from backend.admin import reset_admin_password_with_temporary_password
from backend.log import read_logs, Log
from backend.database_manager import backup_database, restore_database

from site_packages.password import update_own_password
from API_Gateway.authorizer import authorize_user

functions = {
    "add admin": add_user, #id 13
    "add consultant": add_user, #id 6
    "add member": add_member, #id 2
    "backup system": backup_database, #id 10
    "delete admin": delete_user, #id 15
    "delete consultant": delete_user, #id 8
    "delete member record": delete_member, #id 12
    "edit admin": edit_user, #id 14
    "edit consultant": edit_user, #id 7
    "edit member": modify_member, #id 3
    "edit own password": update_own_password, #id 1
    "get log files": read_logs, #id 11
    "get member": get_members, #id 4
    "get users and their roles": get_users, #id 5
    "reset admin password": reset_admin_password_with_temporary_password, #id 16
    "reset consultant password": reset_consultant_password_with_temporary_password, #id 9
    "restore system": restore_database, #id 17
}


def invoke_function(event):
    """
    Invoke the function based on the event provided
    :param event: which is the event dict structured as follows:
        header: {
            token: which is the session token
            permissionId: which is the permission ID
            ...
        }
        body: {
            ...
        }
    :return:
    """
    if not event.get("header"):
        return {"statusCode": 400, "message": "Invalid request"}
    header = event.get("header")

    if not header.get("token") or not header.get("permissionId"):
        return {"statusCode": 400, "message": "Invalid request"}
    token, permission_id = header.get("token"), header.get("permissionId")

    function_name, username = authorize_user(token, permission_id)

    # if there is no body, make one
    if not event.get("body"):
        event["body"] = {}
    event["body"]["invokerUsername"] = username

    if function_name:
        return functions.get(function_name)(event)
    else:
        Log().log_activity(username, "Unauthorized access", "Router: Blocked unauthorized access to the system", True)
        return {"statusCode": 403, "message": "Unauthorized to access this resource"}
