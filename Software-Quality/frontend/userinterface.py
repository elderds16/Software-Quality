from backend.log import Log
from frontend.userinterfacefunctions import Functions_ui  # Import your functions UI
from API_Gateway.login import login, logout
from site_packages.input_safety import safe_input

class UserInterface:
    def __init__(self):
        self.sessionToken = ""
        self.userPermissions = []
        self.log = Log()
        self.current_username = ""

    def loginForm(self):
        statusCode = 0
        while statusCode != 200:
            print("\n---------------------------")
            print("       LOGIN SCREEN        ")
            print("---------------------------")
            username = safe_input(self.current_username, "Enter your username: ").strip()
            password = safe_input(self.current_username, "Enter your password: ").strip()

            response = login(username, password)
            statusCode = response.get("statusCode")

            if statusCode != 200:
                print(f"\nLogin failed! Reason: {response.get('statusMessage')}")
                print("Please try again.")
            else:
                print(f"\nLogin successful! Welcome, {username}.\n")
        
        self.sessionToken = response.get("token")
        self.userPermissions = response.get("permissions")
        #self.userPermissions = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
        self.current_username = username  # Store the current username

        if "passwordAlmostExpired" in response:
            self.update_password_form()

    def update_password_form(self):
        statusCode = 0
        while statusCode != 200:
            print("\n---------------------------")
            print("   PASSWORD EXPIRING SOON   ")
            print("---------------------------")
            print("Your password will expire soon. Please update your password.")
            
            response = Functions_ui.update_own_password(self.sessionToken, self.current_username)
            statusCode = response.get("statusCode")
            
            if statusCode == 200:
                print("Password updated successfully!")
            else:
                print("Failed to update password. Please try again.")

    def display_main_menu(self):
        while True:
            try:
                print("\n---------------------------")
                print("         MAIN MENU         ")
                print("---------------------------")
                menu_option = 1  # Start menu numbering from 1
                menu_mapping = {}  # To map the numbered options to actual functions

                if 5 in self.userPermissions:
                    print(f"[{menu_option}] Check list of users and their roles")
                    menu_mapping[str(menu_option)] = Functions_ui.fetch_and_display_users  # Map option to function
                    menu_option += 1
                if 6 in self.userPermissions:
                    print(f"[{menu_option}] Add a new consultant")
                    menu_mapping[str(menu_option)] = Functions_ui.add_consultant_ui
                    menu_option += 1
                if 7 in self.userPermissions:
                    print(f"[{menu_option}] Modify or update a consultant's account")
                    menu_mapping[str(menu_option)] = Functions_ui.modify_consultant_ui
                    menu_option += 1
                if 8 in self.userPermissions:
                    print(f"[{menu_option}] Delete a consultant's account")
                    menu_mapping[str(menu_option)] = Functions_ui.delete_consultant_ui
                    menu_option += 1
                if 9 in self.userPermissions:
                    print(f"[{menu_option}] Reset a consultant's password")
                    menu_mapping[str(menu_option)] = Functions_ui.reset_consultant_password_ui
                    menu_option += 1
                if 13 in self.userPermissions:
                    print(f"[{menu_option}] Add a new system admin")
                    menu_mapping[str(menu_option)] = Functions_ui.add_system_admin_ui
                    menu_option += 1
                if 14 in self.userPermissions:
                    print(f"[{menu_option}] Modify or update an admin's account")
                    menu_mapping[str(menu_option)] = Functions_ui.modify_admin_ui
                    menu_option += 1
                if 15 in self.userPermissions:
                    print(f"[{menu_option}] Delete an admin's account")
                    menu_mapping[str(menu_option)] = Functions_ui.delete_admin_ui
                    menu_option += 1
                if 16 in self.userPermissions:
                    print(f"[{menu_option}] Reset an admin's password")
                    menu_mapping[str(menu_option)] = Functions_ui.reset_admin_password_ui
                    menu_option += 1
                if 10 in self.userPermissions:
                    print(f"[{menu_option}] Backup up the system")
                    menu_mapping[str(menu_option)] = Functions_ui.backup_system
                    menu_option += 1
                if 17 in self.userPermissions:
                    print(f"[{menu_option}] Restore the system")
                    menu_mapping[str(menu_option)] = Functions_ui.restore_database_ui
                    menu_option += 1
                if 11 in self.userPermissions:
                    print(f"[{menu_option}] View all logs")
                    menu_mapping[str(menu_option)] = Functions_ui.view_logs
                    menu_option += 1
                if 11 in self.userPermissions:
                    print(f"[{menu_option}] View a single log")
                    menu_mapping[str(menu_option)] = Functions_ui.view_single_log
                    menu_option += 1
                if 2 in self.userPermissions:
                    print(f"[{menu_option}] Add a new member")
                    menu_mapping[str(menu_option)] = Functions_ui.add_member_ui
                    menu_option += 1
                if 3 in self.userPermissions:
                    print(f"[{menu_option}] Modify member information")
                    menu_mapping[str(menu_option)] = Functions_ui.modify_member_ui
                    menu_option += 1
                if 12 in self.userPermissions:
                    print(f"[{menu_option}] Delete a member's record")
                    menu_mapping[str(menu_option)] = Functions_ui.delete_member_ui
                    menu_option += 1
                if 4 in self.userPermissions:
                    print(f"[{menu_option}] Search for a member")
                    menu_mapping[str(menu_option)] = Functions_ui.search_member_ui
                    menu_option += 1
                if 1 in self.userPermissions:
                    print(f"[{menu_option}] Update your own password")
                    menu_mapping[str(menu_option)] = Functions_ui.update_own_password
                    menu_option += 1

                print(f"[{menu_option}] Logout")
                menu_mapping[str(menu_option)] = logout  # Map the logout function
                print()

                choice = safe_input(self.current_username, f"Choose an option (1-{menu_option}): ")

                # Execute the corresponding function
                if choice in menu_mapping:
                    if choice == str(menu_option):  # If it's the logout option
                        response = menu_mapping[choice](self.sessionToken, self.current_username)
                        if response and response.get("statusCode") == 200:
                            print("Logged out successfully")
                            self.loginForm()
                        else:
                            print("Error logging out")
                    else:
                        menu_mapping[choice](self.sessionToken, self.current_username)  # Call the mapped function with sessionToken
                    input("Press enter to continue...")

                else:
                    print("Invalid choice, please select a valid option.")
            except KeyboardInterrupt:
                print("\nOperation canceled. Exiting the program.")
                break  # Exit the menu loop gracefully
