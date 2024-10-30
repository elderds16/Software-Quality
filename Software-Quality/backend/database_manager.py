from backend.response import CustomResponse
from backend.log import Log
from site_packages.database import Database
from datetime import datetime, timedelta
from site_packages.encryption import RSA
from site_packages.password import PasswordManager

import os
import shutil
import sys
import zipfile


class DatabaseManger:
    """
    Database manager class to handle database initialization
    """
    def initialize_database(self):
        """
        Initialize the database with the required tables and data
        :return: None
        """
        with Database() as (con, cur):
            # Create table user_role
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                    user_role (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL UNIQUE
                    );
                """
            )

            # Create table permission
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                    permission (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(255) NOT NULL UNIQUE
                    );
                """
            )

            # Create table user
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS 
                    user (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username BLOB NOT NULL UNIQUE,
                        password VARCHAR(255) NOT NULL,
                        password_expiry DATETIME,
                        user_role_id INTEGER,
                        first_name VARCHAR(255),
                        last_name VARCHAR(255),
                        created_on DATETIME,
                        FOREIGN KEY (user_role_id) REFERENCES user_role(id)
                    );
                """
            )

            # Create table member
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS 
                    member (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name VARCHAR(255) NOT NULL,
                        last_name VARCHAR(255),
                        age VARCHAR(255),
                        gender VARCHAR(255),
                        weight VARCHAR(255),
                        address VARCHAR(255),
                        email_address VARCHAR(255),
                        mobile_phone VARCHAR(255),  -- Format: +31-6-DDDDDDDD
                        created_on DATETIME
                    );
                """
            )

            # Create table for user roles and permissions
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS 
                    user_role_has_permission (
                        user_role_id INTEGER,
                        permission_id INTEGER,
                        PRIMARY KEY (user_role_id, permission_id),
                        FOREIGN KEY (user_role_id) REFERENCES user_role(id),
                        FOREIGN KEY (permission_id) REFERENCES permission(id)
                    )
                """
            )

            # Create log table
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS
                    log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date DATETIME,
                        username VARCHAR(255),
                        user_id INTEGER,
                        description_of_activity VARCHAR(255),
                        additional_information VARCHAR(255),
                        suspicious VARCHAR(255),
                        FOREIGN KEY (username) REFERENCES user(username),
                        FOREIGN KEY (user_id) REFERENCES user(id)
                    )
                """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS 
                    session (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,                     
                        session_token varchar(255) NOT NULL UNIQUE,          
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        expires_at DATETIME,                    
                        FOREIGN KEY (user_id) REFERENCES user(id)
                    )
                """
            )

            # Define the roles and their permissions with hardcoded IDs
            roles_permissions = {
                "consultant": [
                    ("edit own password", 1),
                    ("add member", 2),
                    ("edit member", 3),
                    ("get member", 4)
                ],
                "system_administrator": [
                    ("edit own password", 1),
                    ("get users and their roles", 5),
                    ("add consultant", 6),
                    ("edit consultant", 7),
                    ("delete consultant", 8),
                    ("reset consultant password", 9),
                    ("backup system", 10),
                    ("restore system", 17),
                    ("get log files", 11),
                    ("add member", 2),
                    ("edit member", 3),
                    ("delete member record", 12),
                    ("get member", 4)
                ],
                "super_administrator": [
                    ("get users and their roles", 5),
                    ("add consultant", 6),
                    ("edit consultant", 7),
                    ("delete consultant", 8),
                    ("reset consultant password", 9),
                    ("add admin", 13),
                    ("edit admin", 14),
                    ("delete admin", 15),
                    ("reset admin password", 16),
                    ("backup system", 10),
                    ("restore system", 17),
                    ("get log files", 11),
                    ("add member", 2),
                    ("edit member", 3),
                    ("delete member record", 12),
                    ("get member", 4)
                ]
            }

            # Insert roles into the user_role table
            for index, key in enumerate(roles_permissions):
                cur.execute('SELECT 1 FROM user_role WHERE name = :user_role', {"user_role": key})
                if cur.fetchone() is None:
                    cur.execute('INSERT INTO user_role (id, name) VALUES (:id, :user_role)', {"id": index+1, "user_role": key})

            # Insert unique permissions into the permission table with hardcoded IDs
            for permissions in roles_permissions.values():
                for permission, permission_id in permissions:
                    cur.execute('SELECT 1 FROM permission WHERE id = :permission_id', {"permission_id": permission_id})
                    if cur.fetchone() is None:
                        cur.execute('INSERT INTO permission (id, name) VALUES (:permission_id, :permission)',
                                    {"permission_id": permission_id, "permission": permission})

            # Retrieve the ids for the roles and permissions
            cur.execute('SELECT id, name FROM user_role')
            user_roles = {name: id for id, name in cur.fetchall()}

            cur.execute('SELECT id, name FROM permission')
            permissions = {name: id for id, name in cur.fetchall()}

            # Insert mappings into the user_role_has_permission table
            for role, perms in roles_permissions.items():
                role_id = user_roles[role]
                for perm in perms:
                    perm_id = permissions[perm[0]]
                    cur.execute('SELECT 1 FROM user_role_has_permission WHERE user_role_id = :role_id AND permission_id = :permission_id',
                                {"role_id": role_id, "permission_id": perm_id})
                    if cur.fetchone() is None:
                        cur.execute('INSERT INTO user_role_has_permission (user_role_id, permission_id) VALUES (:role_id, :permission_id)',
                                    {"role_id": role_id, "permission_id": perm_id})


            users = [{"username": "super_admin", "password": "Admin_123?", "userRoleId": 3},
                     {"username": "system_admin", "password": "Admin_123?", "userRoleId": 2},
                     {"username": "consultant", "password": "Consultant_123?", "userRoleId": 1}]


            # for each user name RSA encrypt the username
            for user in users:
                encrypted_username = RSA().encrypt(user["username"])
                cur.execute('SELECT 1 FROM user WHERE username = :username', {"username": encrypted_username})
                if cur.fetchone() is None:
                    hashed_password = PasswordManager().hash_password(user["password"])
                    cur.execute('INSERT INTO user (username, password, password_expiry, user_role_id, created_on) VALUES (:username, :password, :password_expiry, :user_role_id, :created_on)',
                                {"username": encrypted_username, "password": hashed_password,
                                 "password_expiry": datetime.now().replace(microsecond=0) + timedelta(days=365),
                                 "user_role_id": user["userRoleId"], "created_on": datetime.now().replace(microsecond=0)})


def backup_database(event):
    """
    Create a backup of the database and log file
    :param event: which is the event dict structured as follows:
        header: {
            invokerUsername: which is the username of the user invoking the backup
        }
    :return: CustomResponse object
    """
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "UM.db")
    # Create the backup directory if it doesn't exist
    backup_dir = os.path.join(os.path.dirname(db_path), "backup DBs")
    os.makedirs(backup_dir, exist_ok=True)  # Create directory if it doesn't exist

    # Get the backup name from the event
    custom_name = event.get("body", {}).get("backup_name")
    if not custom_name:
        return CustomResponse(400, event.get("body", {}).get("invokerUsername"), "Backup name not provided", "Backup name is missing in the event", False)

    # Create the backup filename using the provided name
    backup_filename = f"UM_backup_{custom_name}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Create the zip filename using the provided name
    zip_filename = f"UM_backup_{custom_name}.zip"
    zip_path = os.path.join(backup_dir, zip_filename)

    # Check if the zip backup file already exists
    if os.path.exists(zip_path):
        return CustomResponse(409, event.get("body", {}).get("invokerUsername"), "Backup name already exists", "Duplicate backup name", False)

    try:
        # Copy the database file to the backup location
        shutil.copy2(db_path, backup_path)

        # Path to the encrypted log file
        log_file_path = os.path.join(os.path.dirname(db_path), "logs", "system_log.enc")
        if not os.path.exists(log_file_path):
            log_file_path = None
        else:
            shutil.copy2(log_file_path, os.path.join(backup_dir, f"UM_log_backup_{custom_name}.enc"))

        # Now, zip the backup file (including the log file if it exists)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(backup_path, os.path.basename(backup_path))
            if log_file_path:
                zipf.write(os.path.join(backup_dir, f"UM_log_backup_{custom_name}.enc"), os.path.basename(log_file_path))

        # Optionally remove the .db file and log file after zipping
        os.remove(backup_path)
        if log_file_path:
            os.remove(os.path.join(backup_dir, f"UM_log_backup_{custom_name}.enc"))

        return CustomResponse(200, event.get("body", {}).get("invokerUsername"), "Backup created successfully", f"Backup created named: {backup_filename}", False)
    except Exception as e:
        return CustomResponse(500, event.get("body", {}).get("invokerUsername"), "Backup creation failed", str(e), False)


def restore_database(event):
    """
    Restore the database from a zip backup file
    :param event: which is the event dict structured as follows:
        header: {
            invokerUsername: which is the username of the user invoking the restore
        }
    :return: CustomResponse object
    """
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend", "backup DBs")

    # Check if the backup directory exists
    if not os.path.exists(backup_dir):
        print("No backups to restore, press enter to go back to the main menu.")
        input()  # Wait for user input to return to the main menu
        return

    # List all zip backup files in the directory
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]

    # If no backup files found, notify the user
    if not backups:
        print("No zip backups to restore, press enter to go back to the main menu.")
        input()  # Wait for user input to return to the main menu
        return

    # Sort backups alphabetically
    backups.sort()

    # Loop until the user provides a valid input or leaves it blank
    while True:
        # Display the available backups for the user to choose
        print("Select a zip backup to restore:")
        for i, backup in enumerate(backups, start=1):
            print(f"{i}. {backup}")

        # Prompt for selection
        choice = input(f"Choose an option (1-{len(backups)}): ").strip()

        # If the input is blank, return to the main menu
        if not choice:
            print("No database restored, going back to the main menu.")
            return  # Exit the function and return to the main menu

        # Validate the input: it must be a digit and within the range
        if choice.isdigit() and (1 <= int(choice) <= len(backups)):
            choice = int(choice)  # Convert to integer after validation
            selected_backup = backups[choice - 1]  # Get the selected backup

            # Confirm the restore action
            confirm = input(f"Are you sure you want to restore the backup: {selected_backup}? (y/n): ").strip()

            # Check if the user confirms the restoration
            if confirm.lower() == 'y':
                # Proceed with restoring the database
                backup_path = os.path.join(backup_dir, selected_backup)

                # Extract the zip file
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    temp_restore_dir = os.path.join(backup_dir, 'temp_restore')
                    os.makedirs(temp_restore_dir, exist_ok=True)
                    zip_ref.extractall(temp_restore_dir)

                    # Locate the .db file inside the extracted files
                    extracted_files = os.listdir(temp_restore_dir)
                    db_file = [f for f in extracted_files if f.endswith('.db')][0]  # Assuming there's only one .db file
                    log_file = [f for f in extracted_files if f.endswith('.enc')]  # Look for the log file if it exists

                    # Set the paths to the extracted database and log files
                    extracted_db_path = os.path.join(temp_restore_dir, db_file)
                    extracted_log_path = os.path.join(temp_restore_dir, log_file[0]) if log_file else None

                # Restore the database file
                current_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "UM.db")

                # Close the current connection to the database
                Database.close_all_connections()

                # Remove the existing UM.db
                if os.path.exists(current_db_path):
                    os.remove(current_db_path)

                # Copy the extracted .db file to the current location and rename it
                shutil.copy(extracted_db_path, current_db_path)
                print(f"Successfully restored {selected_backup}")

                # Restore the log file if it exists
                if extracted_log_path:
                    log_restore_path = os.path.join(os.path.dirname(current_db_path), "logs", "system_log.enc")

                    # Remove the current log file if it exists
                    if os.path.exists(log_restore_path):
                        os.remove(log_restore_path)

                    # Copy the new log file and rename it
                    shutil.copy(extracted_log_path, log_restore_path)
                    print("Successfully restored log")

                # Clean up the temporary restore directory
                shutil.rmtree(temp_restore_dir)

                Log().log_activity("system_admin", "Database restored",
                                   f"Database restored from backup: {selected_backup}", False)

                # Restart the application
                answer = input("Application needs to be restarted to apply changes. Restart now? (y/n): ").strip()

                if answer.lower() != 'y':
                    print("You don't have a choice anyway, restarting the application.")
                python = sys.executable
                os.execl(python, python, *sys.argv)

            else:
                print("Restore cancelled.")
                return  # Exit after cancelling the restore

        else:
            print(f"Invalid selection. Please enter a number between 1 and {len(backups)}.")
