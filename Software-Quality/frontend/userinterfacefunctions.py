from API_Gateway.router import invoke_function
import re
import string

from site_packages.input_safety import safe_input, is_email_valid, is_address_valid, is_age_valid, is_weight_valid, is_mobile_valid, is_name_valid, is_gender_valid


class Functions_ui:

    MAX_NAME_LENGTH = 15
    MAX_EMAIL_LENGTH = 25
    MAX_ADDRESS_LENGTH = 20
    MAX_GENDER_LENGTH = 15
    MAX_WEIGHT_LENGTH = 4

    @staticmethod
    def validate_name(name):
        if len(name) <= Functions_ui.MAX_NAME_LENGTH and re.match(r'^[a-zA-Z\s]+$', name):
            return name
        else:
            raise ValueError(f"Name must be {Functions_ui.MAX_NAME_LENGTH} characters or less, and only contain letters and spaces.")

    @staticmethod
    def validate_email(email_address):
        if is_email_valid(email_address):
            return email_address
        else:
            raise ValueError(f"Invalid email address or length exceeds {Functions_ui.MAX_EMAIL_LENGTH} characters.")

    @staticmethod
    def validate_address(address):
        if is_address_valid(address):
            return address
        else:
            raise ValueError(f"Address must be {Functions_ui.MAX_ADDRESS_LENGTH} characters or less and only contain letters, numbers, commas, hyphens, or periods.")

    @staticmethod
    def validate_age(age_str):
        if age_str.isdigit():
            if is_age_valid(age_str):
                return age_str
            else:
                raise ValueError("Age must be between 18 and 125.")
        else:
            raise ValueError("Please enter a valid age.")

    @staticmethod
    def validate_weight(weight_str, current_username):
        if is_weight_valid(weight_str):
            weight = float(weight_str)
            while True:
                weight_unit = safe_input(current_username, "Is this weight in kg or pounds? (Enter '[1]' for kg or '[2]' for lbs): ").strip().lower()
                if weight_unit in ['1', '2']:
                    if weight_unit == '2':
                        weight = round(weight * 0.453592, 1)  # Convert pounds to kg
                    return weight
                else:
                    print("Invalid input. Please enter '[1]' for kg or '[2]' for lbs.")
        else:
            raise ValueError(f"Please enter a valid weight (up to {Functions_ui.MAX_WEIGHT_LENGTH} characters, and less than 500 kg).")

    @staticmethod
    def validate_mobile(mobile_str):
        if is_mobile_valid(mobile_str):
            return f"+31 6-{mobile_str}"
        else:
            raise ValueError("Mobile phone must be exactly 8 digits.")

    @staticmethod
    def validate_gender(gender):
        gender = gender.lower()
        if is_gender_valid(gender):
            if gender in ['male', 'm']:
                return 'Male'
            elif gender in ['female', 'f']:
                return 'Female'
            elif gender in ['other', 'o']:
                return 'Other'
        else:
            raise ValueError("Gender must be 'Male', 'Female', or 'Other' (or 'M', 'F', 'O').")

    @staticmethod
    def get_input(prompt, validation_func, current_username, allow_skip=True):
        while True:
            user_input = safe_input(current_username, prompt).strip()
            if not user_input and allow_skip:  # Skip if input is empty and skipping is allowed
                return None
            try:
                return validation_func(user_input) if user_input else None
            except ValueError as e:
                print(e)

    @staticmethod
    def add_member_ui(sessionToken, current_username):
        # Collect input with validations using the new validation functions
        first_name = Functions_ui.get_input("Enter first name: ", Functions_ui.validate_name, current_username)
        if first_name is None: return
        last_name = Functions_ui.get_input("Enter last name: ", Functions_ui.validate_name, current_username)
        if last_name is None: return
        address = Functions_ui.get_input("Enter address: ", Functions_ui.validate_address, current_username)
        if address is None: return
        email_address = Functions_ui.get_input("Enter email address: ", Functions_ui.validate_email, current_username)
        if email_address is None: return
        age = Functions_ui.get_input("Enter age (18-125): ", Functions_ui.validate_age, current_username)
        if age is None: return
        gender = Functions_ui.get_input("Enter gender (Male/Female/Other): ", Functions_ui.validate_gender, current_username)
        if gender is None: return
        weight = Functions_ui.get_input("Enter weight: ", lambda w: Functions_ui.validate_weight(w, current_username), current_username)
        if weight is None: return
        mobile_phone = Functions_ui.get_input("Enter your mobile phone (8 digits): (+31 6-)", Functions_ui.validate_mobile, current_username)
        if mobile_phone is None: return

        # Clean whitespace in names, address, email, and gender
        first_name = Functions_ui.clean_whitespace(first_name)
        last_name = Functions_ui.clean_whitespace(last_name)
        address = Functions_ui.clean_whitespace(address)
        email_address = Functions_ui.clean_whitespace(email_address)
        gender = Functions_ui.clean_whitespace(gender)

        # Create the event object
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 2  # Permission ID for adding a member
            },
            "body": {
                "firstName": first_name,
                "lastName": last_name,
                "age": age,
                "gender": gender,
                "weight": weight,
                "address": address,
                "emailAddress": email_address,
                "mobilePhone": mobile_phone
            }
        }

        # Call the add_member function
        response = invoke_function(event)

        if response['statusCode'] == 200:
            print(f"Member added successfully! Membership ID: {response.get('membershipId', 'N/A')}")
        else:
            print(response.get('message', 'An error occurred.'))

    @staticmethod
    def modify_member_ui(sessionToken, current_username):
        # Fetch members from the database
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 4  # Permission ID for fetching members
            }
        }
        members_response = invoke_function(event)

        if members_response['statusCode'] == 200:
            members = members_response['members']
            if not members:
                print("No members found to modify.")
                return

            # Sort and display members
            members.sort(key=lambda x: (x['last_name'] is None, x['last_name'] or ''))
            print("\n--- Members List ---")
            for index, member in enumerate(members):
                print(f"{index + 1}. ID: {member['id']} | Name: {member['first_name']} {member['last_name']}")

            # Prompt user to select a member by index
            try:
                selection = int(safe_input(current_username, "Enter the number of the member to modify: ")) - 1
                if selection < 0 or selection >= len(members):
                    print("Invalid selection. Please choose a valid number.")
                    return
                member_id_to_modify = members[selection]['id']
            except ValueError:
                print("Invalid input. Please enter a number.")
                return

            updated_fields = {}

            # Use the same validation functions for modifying fields
            first_name = Functions_ui.get_input("Enter new first name (or press Enter to skip): ", Functions_ui.validate_name, current_username)
            if first_name is not None:
                updated_fields["firstName"] = Functions_ui.clean_whitespace(first_name).title()

            last_name = Functions_ui.get_input("Enter new last name (or press Enter to skip): ", Functions_ui.validate_name, current_username)
            if last_name is not None:
                updated_fields["lastName"] = Functions_ui.clean_whitespace(last_name).title()

            address = Functions_ui.get_input("Enter new address (or press Enter to skip): ", Functions_ui.validate_address, current_username)
            if address is not None:
                updated_fields["address"] = Functions_ui.clean_whitespace(address)

            email_address = Functions_ui.get_input("Enter new email address (or press Enter to skip): ", Functions_ui.validate_email, current_username)
            if email_address is not None:
                updated_fields["emailAddress"] = Functions_ui.clean_whitespace(email_address)

            age = Functions_ui.get_input("Enter new age (or press Enter to skip): ", Functions_ui.validate_age, current_username)
            if age is not None:
                updated_fields["age"] = age

            gender = Functions_ui.get_input("Enter new gender (or press Enter to skip): ", Functions_ui.validate_gender, current_username)
            if gender is not None:
                updated_fields["gender"] = Functions_ui.clean_whitespace(gender)

            weight = Functions_ui.get_input("Enter new weight (or press Enter to skip): ", lambda w: Functions_ui.validate_weight(w, current_username), current_username)
            if weight is not None:
                updated_fields["weight"] = weight

            mobile_phone = Functions_ui.get_input("Enter your mobile phone (8 digits): (+31 6-) ", Functions_ui.validate_mobile, current_username)
            if mobile_phone is not None:
                updated_fields["mobilePhone"] = mobile_phone

            # Show updated fields for confirmation before saving
            if updated_fields:
                print("\n--- Review Changes ---")
                for field, value in updated_fields.items():
                    print(f"{field}: {value}")

                confirm = safe_input(current_username, "\nDo you want to save these changes? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("Changes discarded.")
                    return

                # Call modify_member function
                event = {
                    "header": {
                        "token": sessionToken,
                        "permissionId": 3  # Permission ID for modifying a member
                    },
                    "body": {
                        "memberId": member_id_to_modify,
                        **updated_fields
                    }
                }
                response = invoke_function(event)

                if response['statusCode'] == 200:
                    print(f"Member record with ID: {member_id_to_modify} has been updated successfully!")
                else:
                    print("Failed to update member.")
            else:
                print("No changes were made.")
        else:
            print("Failed to fetch members.")


    @staticmethod
    def clean_whitespace(text):
        """
        Verwijder overtollige spaties, inclusief meerdere spaties tussen woorden.
        """
        # Verwijder spaties aan de randen en vervang meerdere spaties door één spatie
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def validate_input_length(prompt, max_length, current_username):
        """
        Helper functie om de lengte van de input te valideren.
        Zorgt ervoor dat de invoer niet langer is dan max_length.
        """
        while True:
            user_input = safe_input(current_username, prompt).strip()  # Verwijder extra spaties aan het begin en eind
            if user_input == "":
                return user_input  # Allow skipping by pressing Enter
            if len(user_input) <= max_length:
                return user_input
            else:
                print(f"Input must be {max_length} characters or less and cannot be empty.")

    @staticmethod
    def validate_name_input(prompt, max_length, current_username):
        """
        Helper functie om de lengte van de input te valideren en ervoor te zorgen dat er geen getallen in de naam staan.
        Zorgt ervoor dat de invoer niet langer is dan max_length en geen cijfers bevat.
        """
        while True:
            user_input = safe_input(current_username, prompt).strip()  # Verwijder extra spaties aan het begin en eind
            if user_input == "":
                return user_input  # Allow skipping by pressing Enter
            if len(user_input) <= max_length and not any(char.isdigit() for char in user_input) and re.match(r'^[a-zA-Z\s]+$', user_input):
                return user_input
            else:
                print(f"Input must be {max_length} characters or less, cannot be empty, must not contain numbers, and must not contain symbols.")



    @staticmethod
    def delete_member_ui(sessionToken, current_username):
        def validate_member_selection(selection, members):
            """
            Validate the user's selection to ensure it's a valid index.
            - Whitelist: Only allow numbers as input
            - Check for valid range
            """
            selection = selection.strip()  # Clean up whitespace

            # Check for empty input
            if not selection:
                return None, "No input provided, returning to the main menu."

            # Ensure the input is a number
            if not selection.isdigit():
                return None, "Invalid input. Please enter a number."

            # Convert to an integer and check if within the range of available members
            selection_num = int(selection)
            if selection_num < 1 or selection_num > len(members):
                return None, "Invalid selection. Please choose a valid number."

            # Return the valid selection (adjusted for 0-based indexing)
            return selection_num - 1, None

        try:
            # Prepare the event object for fetching members
            event = {
                "header": {
                    "token": sessionToken,
                    "permissionId": 4  # Permission ID for fetching members
                }
            }

            # Fetch members from the database
            members_response = invoke_function(event)
            if members_response['statusCode'] == 200:
                members = members_response['members']

                if not members:
                    print("No members found to delete.")
                    return

                # Sort members by last name
                members.sort(key=lambda x: (x['last_name'] is None, x['last_name'] or ''))

                # Display members with index numbers
                print("\n--- Members List ---")
                for index, member in enumerate(members):
                    print(f"{index + 1}. ID: {member['id']} | Name: {member['first_name']} {member['last_name']}")

                while True:
                    # Ask user for the index of the member to delete
                    member_selection = safe_input(current_username, "Enter the number of the member to delete (or press Enter to return to the main menu): ").strip()

                    # Validate the user's input
                    valid_selection, validation_error = validate_member_selection(member_selection, members)

                    # Handle invalid input (keep looping if the input is invalid)
                    if validation_error:
                        if not member_selection:  # If input is blank, return to the main menu
                            print(validation_error)
                            return
                        print(validation_error)
                        continue  # Keep looping and ask for input again if invalid

                    # Get the member ID to delete
                    member_id_to_delete = members[valid_selection]['id']

                    # Confirmation prompt
                    while True:
                        confirmation = safe_input(current_username, f"Are you sure you want to delete the member with ID {member_id_to_delete}? (y/n or type 'menu' for Main Menu): ").strip().lower()

                        # Handle user input for confirmation
                        if confirmation == 'y':
                            # Create the event object for deletion
                            event = {
                                "header": {
                                    "token": sessionToken,
                                    "permissionId": 12  # Permission ID for deleting a member
                                },
                                "body": {
                                    "memberId": member_id_to_delete
                                }
                            }

                            # Call the delete_member function with the member ID
                            response = invoke_function(event)

                            # Check the response and print the appropriate message
                            if response['statusCode'] == 200:
                                print(f"Member record with ID: {member_id_to_delete} is removed!")
                            else:
                                print("Failed to delete member.")
                            break  # Exit the loop after deletion
                        elif confirmation == 'n':
                            print("Deletion cancelled.")
                            break  # Exit the loop and go back to asking for another ID
                        elif confirmation == 'menu':
                            print("Going back to main menu.")
                            return  # Exit the function and go back to the main menu
                        else:
                            print("Please input y/n or 'menu' to go back to main menu.")
                    break  # Exit the outer loop after deletion or cancellation

            else:
                print("Failed to fetch members.")
        except KeyboardInterrupt:
            print("\nOperation canceled. Exiting the program.")
            exit(0)  # Exit the program completely







    @staticmethod
    def backup_system(sessionToken, current_username):
        def validate_backup_name(backup_name):
            """
            Validate backup name to ensure it meets:
            - Max length (20 characters)
            - No null bytes
            - Alphanumeric, underscores, hyphens only
            - No leading/trailing or excessive whitespace
            """
            MAX_BACKUP_NAME_LENGTH = 20
            MIN_BACKUP_NAME_LENGTH = 3

            # Clean up whitespace
            cleaned_name = ' '.join(backup_name.split()).strip()

            # Length check
            if len(cleaned_name) < MIN_BACKUP_NAME_LENGTH or len(cleaned_name) > MAX_BACKUP_NAME_LENGTH:
                raise ValueError(f"Backup name must be between {MIN_BACKUP_NAME_LENGTH} and {MAX_BACKUP_NAME_LENGTH} characters.")

            # Whitelisting valid characters
            if not re.match(r'^[a-zA-Z0-9_-]+$', cleaned_name):
                raise ValueError("Backup name can only contain letters, numbers, underscores, and hyphens.")

            return cleaned_name

        while True:
            try:
                # Ask the user for a custom backup name
                custom_name = safe_input(current_username, "Enter a name for the backup (or press Enter to cancel): ").strip()

                # Check if the input is blank
                if not custom_name:
                    print("No backup created, going back to main menu.")
                    return  # Exit the function and go back to the main menu

                # Validate backup name
                valid_name = validate_backup_name(custom_name)

                # Call the backup function from Database Manager with the validated name
                event = {
                    "header": {
                        "token": sessionToken,
                        "permissionId": 10  # Permission ID for backing up the system
                    },
                    "body": {
                        "backup_name": valid_name  # Pass the validated name
                    }
                }

                backup_response = invoke_function(event)

                # Check if the backup name already exists
                if backup_response.get('statusCode') == 409:
                    print("Backup name already exists, please choose another name.")
                    continue  # Prompt the user to enter another name

                print(backup_response.get('message'))  # Print the backup response
                break  # Exit after successful backup

            except ValueError as e:
                print(e)  # Display the validation error and prompt the user again


    @staticmethod
    def restore_database_ui(sessionToken, current_username):
        # Prepare the event object for restoring the database
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 17  # Permission ID for restoring the database
            }
        }

        # Call the restore_database function with the backup path
        invoke_function(event)



    @staticmethod
    def fetch_and_display_users(sessionToken, current_username):
        users_response = Functions_ui.request_get_users(sessionToken, current_username)
        if users_response and users_response['statusCode'] == 200:
            users = users_response['users']

            # Filter out users with specific usernames
            filtered_users = [
                user for user in users
                if user['username'] not in ['super_admin', 'system_admin', 'consultant']
            ]

            Functions_ui.display_users(filtered_users)
        else:
            print("Failed to fetch users.")



    @staticmethod
    def display_users(users):
        if not users:
            print("No users available.")
            return

        # Define field widths for better alignment
        username_width = max(len(user['username']) for user in users) + 2  # Adding some padding
        role_width = max(len(user['user_role_name']) for user in users) + 2  # Adding some padding

        # Print header
        print(f"{'Index':<5} {'Username':<{username_width}} {'Role':<{role_width}}")
        print("-" * (5 + username_width + role_width))  # Separator line

        # Display users with formatted output
        for index, user in enumerate(users):
            print(f"{index + 1:<5} {user['username']:<{username_width}} {user['user_role_name']:<{role_width}}")




    @staticmethod
    def request_get_users(sessionToken, current_username):
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 5  # Permission ID for viewing users
            },
            "body": {}  # Adding an empty body
        }
        #print(f"Request Event: {event}")  # Debug print to see the event object
        response = invoke_function(event)
        #print(f"Invoke Function Response: {response}")  # Debug print to see the response
        return response




    @staticmethod
    def add_consultant_ui(sessionToken, current_username):
        # Vraag gebruiker om username en valideer
        while True:
            username = safe_input(current_username, "Enter username (or press Enter to cancel): ").strip().lower()
            
            
            if not username:  # Als invoer leeg is, annuleer het proces
                print("User not made, going back to Main Menu.")
                return  # Stop de functie en keer terug naar het hoofdmenu
            
            is_valid, message = Functions_ui.validate_username(username)
            if is_valid:
                break
            else:
                print(message)

        # Vraag gebruiker om wachtwoord en valideer
        while True:
            password = safe_input(current_username, "Enter password (or press Enter to cancel): ").strip()
           
            
            if not password:  # Als invoer leeg is, annuleer het proces
                print("User not made, going back to Main Menu.")
                return  # Stop de functie en keer terug naar het hoofdmenu
            
            is_valid, message = Functions_ui.validate_password(password)
            if is_valid:
                break
            else:
                print(message)

        # Als beide validaties slagen, maak het event object aan om de consultant toe te voegen
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 6  # Permission ID voor het toevoegen van een consultant
            },
            "body": {
                "username": username,
                "password": password,
                "userRoleId": 1  # Consultant role ID
            }
        }

        # Verwerk de API-aanroep om de consultant toe te voegen
        response = invoke_function(event)

        # Controleer of de API-aanroep succesvol was
        if response and response.get("statusCode") != 200:
            print("Something went wrong: ", response.get("message"))
        elif response:
            print(response.get("message"))


    @staticmethod
    def modify_consultant_ui(sessionToken, current_username):
        try:
            # Fetch all users from the database
            event = {
                "header": {
                    "token": sessionToken,
                    "permissionId": 5  # Permission ID for viewing users
                },
                "body": {}
            }
            users_response = invoke_function(event)

            if users_response.get("statusCode") == 200:
                users = users_response.get("users")

                # Filter to get only consultant accounts excluding specific usernames
                consultants = [
                    user for user in users
                    if user['user_role_id'] == 1 and user['username'] not in ['system_admin', 'super_admin', 'consultant']
                ]

                # Check if there are any consultants available for modification
                if not consultants:
                    print("No consultant accounts available for modification.")
                    return

                # Sort consultants for display
                consultants.sort(key=lambda x: (x['username'] if x['username'] is not None else ''))

                # Display consultants
                Functions_ui.display_users(consultants)

                # Ask user for the index of the consultant to modify
                selection_input = safe_input(current_username, "Enter the number of the consultant to modify (leave blank to cancel): ").strip()
            
                # If the input is blank, go back to the main menu
                if not selection_input:
                    print("No selection made, going back to the main menu.")
                    return

                try:
                    selection = int(selection_input) - 1
                    if selection < 0 or selection >= len(consultants):
                        print("Invalid selection. Please choose a valid number.")
                        return
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    return

                # Get the selected consultant's details
                selected_consultant = consultants[selection]
                consultant_id = selected_consultant['id']

                print(f"Modifying account for {selected_consultant['username']}")

                # Get new username with immediate validation
                while True:
                    new_username = safe_input(current_username, "Enter new username (leave blank to keep current): ").strip().lower()

                    if not new_username:  # Keep current username if blank
                        new_username = selected_consultant['username']
                        break

                    # Validate the new username
                    is_valid, message = Functions_ui.validate_username(new_username)
                    if is_valid:
                        break  # Exit loop if valid
                    else:
                        print(message)  # Show error message and prompt for the username again

                # Get new password with validation loop
                while True:
                    new_password = safe_input(current_username, "Enter new password (leave blank to keep current): ").strip()

                    # If blank, keep current password and move on
                    if not new_password:
                        break

                    # Validate the new password
                    is_valid, message = Functions_ui.validate_password(new_password)
                    if is_valid:
                        break  # Exit loop if valid
                    else:
                        print(message)  # Show error message and prompt for the password again

                # Always ask for role change
                new_role_input = safe_input(current_username, "Enter the number of the new role (1 for Consultant, 2 for System Administrator, leave blank to keep current): ").strip()

                if not new_role_input:
                    new_role_id = selected_consultant['user_role_id']  # Keep current role if no input
                else:
                    new_role_id = 1 if new_role_input == '1' else 2  # Set new role ID based on input

                # If no changes are made, inform the user
                if not new_password and new_username == selected_consultant['username'] and new_role_id == selected_consultant['user_role_id']:
                    print("No changes made. Going back to the main menu.")
                    return

                # Prepare the event for modifying the user
                event = {
                    "header": {"token": sessionToken, "permissionId": 7},  # Permission ID for modifying users
                    "body": {
                        "userId": consultant_id,
                        "username": new_username,
                        "user_role_id": new_role_id  # Add role ID
                    }
                }

                # Only add password if a new password is provided
                if new_password:
                    event['body']['password'] = new_password

                # Call the edit_user function to modify the consultant details
                response = invoke_function(event)  # Assuming edit_user returns a response

                # Check and print the response
                if response is not None:
                    if response.get("statusCode") == 200:
                        print("Consultant updated successfully!")
                    else:
                        print("Failed to update consultant:", response.get("message"))
                else:
                    print("No response received from edit_user.")
            else:
                print("Failed to fetch users.", users_response.get("message"))
        except Exception as e:
            print(f"An error occurred: {e}")


    @staticmethod
    def delete_consultant_ui(session_token, current_username):
        def validate_consultant_id(consultant_id, consultants):

            # Clean up whitespace
            consultant_id = consultant_id.strip()

            # Check for empty input
            if not consultant_id:
                return None, "No ID provided, returning to the main menu."

            # Check if the ID is numeric
            if not consultant_id.isdigit():
                return None, "Consultant ID must only contain numbers."

            # Find the maximum length of the IDs based on the current consultants
            max_id_length = max(len(str(consultant["id"])) for consultant in consultants)

            # Check if the input ID length exceeds the max length of existing IDs
            if len(consultant_id) > max_id_length:
                return None, f"Consultant ID must not exceed {max_id_length} characters."

            # Check if the ID exists in the list of consultants
            consultant_exists = any(str(consultant["id"]) == consultant_id for consultant in consultants)
            if not consultant_exists:
                return None, "Consultant ID does not exist, please choose another."

            # Return the valid consultant ID
            return consultant_id, None

        # Prepare the event object for fetching consultants
        event = {
            "header": {
                "token": session_token,
                "permissionId": 5,  # Permission ID for viewing users
                "userRoleId": 1  # User role ID for consultants
            }
        }

        # Get the list of consultants from the backend
        consultant_response = invoke_function(event)

        if consultant_response.get("statusCode") == 200:
            consultants = consultant_response.get("users")

            # Exclude the consultant account with username "consultant"
            consultants = [consultant for consultant in consultants if consultant['username'] != "consultant"]

            # Check if there are any consultants available for deletion
            if not consultants:
                print("No consultant accounts available for deletion.")
                safe_input(current_username, "press enter to continue...")  # Prompt user to press enter
                return  # Exit the function if no consultants are available

            while True:
                print("\n--- Consultants List ---")
                for consultant in consultants:
                    print(f"ID: {consultant['id']}, Username: {consultant['username']}")

                while True:
                    # Prompt user for consultant ID
                    consultant_id_input = safe_input(current_username, "Enter the ID of the consultant to delete (or press Enter to return to the main menu): ").strip()

                    # Validate the consultant ID
                    valid_consultant_id, validation_error = validate_consultant_id(consultant_id_input, consultants)

                    # Handle blank input (user presses Enter) - Return to main menu
                    if consultant_id_input == "":
                        print("No ID provided, returning to the main menu.")
                        return

                    # Handle validation errors
                    if validation_error:
                        print(validation_error)
                        continue  # Reprompt the user to enter the ID
                    else:
                        break  # Valid consultant ID provided

                # Confirm deletion
                confirm = safe_input(current_username, f"Are you sure you want to delete consultant ID {valid_consultant_id}? (y/n): ").strip().lower()

                if confirm == 'y':
                    # Prepare the event object for deleting the consultant
                    event = {
                        "header": {"token": session_token, "permissionId": 8},  # Permission ID for deletion
                        "body": {
                            "userId": valid_consultant_id
                        }
                    }

                    # Call the delete consultant function
                    response = invoke_function(event)

                    # Check the response and print a message
                    if response is not None:
                        if response.get("statusCode") == 200:
                            print("Consultant deleted successfully!")
                            break  # Exit and return to main menu after successful deletion
                        else:
                            print("Failed to delete consultant:", response.get("message"))
                    else:
                        print("No response received from deleting consultant.")
                else:
                    print("Deletion cancelled.")
                    continue  # Go back to ask for another consultant to delete

            # After deletion or cancellation, return to the main menu
            print("Returning to the main menu.")
        else:
            print("Failed to fetch consultants.")



            

    @staticmethod
    def view_logs(sessionToken, current_username):
        # Get the logs through the invoke function
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 11  # Permission ID for viewing logs
            }
        }
        response = invoke_function(event)

        logs = []
        if response and response.get("statusCode") == 200:
            logs = response.get("logs")
        else:
            print("Failed to fetch logs.")

        if logs:
            # Define a default column width
            default_widths = {
                'id': 5,
                'date': 15,
                'time': 10,
                'username': 15,
                'description': 30,
                'additional_info': 30,
                'suspicious': 10
            }

            # Find the maximum length for each column
            for log_entry in logs:
                default_widths['description'] = max(default_widths['description'], len(log_entry['description']))
                default_widths['additional_info'] = max(default_widths['additional_info'],
                                                        len(log_entry['additional_info']))

            # Prepare header with adjusted widths
            header = (
                f"{'ID':<{default_widths['id']}} "
                f"{'Date':<{default_widths['date']}} "
                f"{'Time':<{default_widths['time']}} "
                f"{'Username':<{default_widths['username']}} "
                f"{'Description':<{default_widths['description']}} "
                f"{'Additional Info':<{default_widths['additional_info']}} "
                f"{'Suspicious':<{default_widths['suspicious']}}"
            )
            print(header)
            print("-" * len(header))  # Print a separator line

            # Loop through each log entry and format the data
            for log_entry in logs:
                # Safely retrieve values from the log entry, defaulting to an empty string if None
                log_id = log_entry['id'] if log_entry['id'] is not None else ""
                log_date = log_entry['date'] if log_entry['date'] is not None else ""
                log_time = log_entry['time'] if log_entry['time'] is not None else ""
                username = log_entry['username'] if log_entry['username'] is not None else ""
                description = log_entry['description'] if log_entry['description'] is not None else ""
                additional_info = log_entry['additional_info'] if log_entry['additional_info'] is not None else ""
                suspicious_status = "\033[91mYES\033[0m" if log_entry['suspicious'] else "no"  # Convert boolean to Yes/No

                # Format the row with safe values
                row = (
                    f"{log_id:<{default_widths['id']}} "
                    f"{log_date:<{default_widths['date']}} "
                    f"{log_time:<{default_widths['time']}} "
                    f"{username:<{default_widths['username']}} "
                    f"{description:<{default_widths['description']}} "
                    f"{additional_info:<{default_widths['additional_info']}} "
                    f"{suspicious_status:<{default_widths['suspicious']}}"
                )
                print(row)  # Print each log entry formatted

        else:
            print("No logs available.")



    @staticmethod
    def view_single_log(sessionToken, current_username):
        # Get the logs through the invoke function
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 11  # Permission ID for viewing logs
            }
        }
        response = invoke_function(event)

        logs = []
        if response and response.get("statusCode") == 200:
            logs = response.get("logs")
        else:
            print("Failed to fetch logs.")

        if logs:
            while True:
                print("\n--- Available Logs ---")

                # Define max lengths for each field
                max_id_length = max(len(str(log_entry['id'])) for log_entry in logs)
                max_date_length = max(
                    len(log_entry['date']) if log_entry['date'] is not None else 0 for log_entry in logs)
                max_time_length = max(
                    len(log_entry['time']) if log_entry['time'] is not None else 0 for log_entry in logs)
                max_username_length = max(
                    len(log_entry['username']) if log_entry['username'] is not None else 0 for log_entry in logs)
                max_suspicious_length = max(len("Yes" if log_entry['suspicious'] else "No") for log_entry in logs)

                # Prepare header with adjusted widths
                header = (
                    f"{'ID':<{max_id_length + 2}} "
                    f"{'Date':<{max_date_length + 2}} "
                    f"{'Time':<{max_time_length + 2}} "
                    f"{'Username':<{max_username_length + 2}} "
                    f"{'Suspicious':<{max_suspicious_length + 2}}"
                )
                print(header)
                print("-" * len(header))  # Print a separator line

                # Display IDs, Date, Time, Username, and Suspicious status
                for log_entry in logs:
                    suspicious_status = "\033[91mYES\033[0m" if log_entry['suspicious'] else "No"
                    row = (
                        f"{log_entry['id']:<{max_id_length + 2}} "
                        f"{(log_entry['date'] if log_entry['date'] is not None else ''):<{max_date_length + 2}} "
                        f"{(log_entry['time'] if log_entry['time'] is not None else ''):<{max_time_length + 2}} "
                        f"{(log_entry['username'] if log_entry['username'] is not None else ''):<{max_username_length + 2}} "
                        f"{suspicious_status:<{max_suspicious_length + 2}}"
                    )
                    print(row)

                # Ask user to select a log by ID
                while True:
                    log_id_input = safe_input(current_username, "\nEnter the ID of the log you want to view (or press Enter to go back): ").strip()

                    # Handle blank input: go back to the main menu
                    if not log_id_input:
                        print("No log selected, going back to main menu.")
                        return

                    # Check if the input is a valid integer
                    if not log_id_input.isdigit():
                        print("Invalid input. Please enter a valid number.")
                        continue  # Reprompt the user

                    log_id = int(log_id_input)

                    # Check if the log ID is within the available range
                    log_ids = [log_entry['id'] for log_entry in logs]
                    if log_id not in log_ids:
                        print(f"Invalid input. No log found with ID {log_id}.")
                        continue  # Reprompt the user

                    # Valid input, so break out of the loop
                    break

                # Search for the log with the selected ID
                selected_log = next((log_entry for log_entry in logs if log_entry['id'] == log_id), None)

                # Display the selected log's details if found
                if selected_log:
                    print("\n--- Log Details ---")
                    print(f"ID: {selected_log['id']}")
                    print(f"Date: {selected_log['date'] if selected_log['date'] is not None else 'N/A'}")
                    print(f"Time: {selected_log['time'] if selected_log['time'] is not None else 'N/A'}")
                    print(f"Username: {selected_log['username'] if selected_log['username'] is not None else 'N/A'}")
                    print(f"Description: {selected_log['description'] if selected_log['description'] is not None else 'N/A'}")
                    print(f"Additional Info: {selected_log['additional_info'] if selected_log['additional_info'] is not None else 'N/A'}")
                    print("Suspicious: " + ("\033[91mYES\033[0m" if selected_log['suspicious'] else "No"))
                    print("--------------------\n")

                # Ask if the user wants to view another log
                while True:
                    another = safe_input(current_username, "Do you want to view another log? (y/n): ").strip().lower()

                    # Handle blank input: return to the main menu
                    if not another:
                        print("Going back to the main menu.")
                        return

                    # If user enters 'n', exit the loop and return to the main menu
                    if another == 'n':
                        print("Returning to main menu.")
                        return  # Exit the function

                    # If user enters 'y', break and continue to view another log
                    if another == 'y':
                        break
        else:
            print("No logs available.")




    @staticmethod
    def add_system_admin_ui(sessionToken, current_username):
        # Directly set the user role to System Administrator (userRoleId = 2)
        user_role_id = 2

        # Vraag gebruiker om username en valideer
        while True:
            username = safe_input(current_username, "Enter username for the new System Administrator (leave blank to return to main menu): ").strip().lower()
        
            if not username:  # Check if the input is left blank
                print("Username not provided, going back to the main menu.")
                return  # Exit and return to the main menu
            is_valid, message = Functions_ui.validate_username(username)
            if is_valid:
                break
            else:
                print(message)

        # Vraag gebruiker om wachtwoord en valideer
        while True:
            password = safe_input(current_username, "Enter password for the new System Administrator (leave blank to return to main menu): ").strip()
        
            if not password:  # Check if the input is left blank
                print("Password not provided, going back to the main menu.")
                return  # Exit and return to the main menu
            is_valid, message = Functions_ui.validate_password(password)
            if is_valid:
                break
            else:
                print(message)

        # Construct event
        event = {
            "header": {"token": sessionToken, "permissionId": 13},  # Permission ID for adding admin
            "body": {
                "username": username,
                "password": password,
                "userRoleId": user_role_id  # Use the System Administrator role
            }
        }

        # Call the invoke function to add the admin
        response = invoke_function(event)

        # Check the response and prepare a user-friendly message
        if response.get("statusCode") == 200:
            print()  # Blank line for spacing

            # Set the width for formatting
            field_width = 30  # Adjust this width as needed

            # Display success message for System Administrator
            success_message = (
                f"{'System Administrator Successfully created!':<{field_width}}\n"
                f"{'Username:':<{field_width}} {username}\n"
                f"{'Password:':<{field_width}} {password}"
            )
            print(success_message)
        else:
            print()  # Blank line for spacing
            print(response.get("message"))




    @staticmethod
    def delete_admin_ui(sessionToken, current_username):
        def validate_selection_input(selection_input, max_length):
            """
            Validates the user's input for selecting which admin to delete.
            - Whitespace is cleaned.
            - Input is numeric and within the valid range.
            """
            selection_input = selection_input.strip()  # Clean whitespace
        
            # Check for empty input (go back to main menu if blank)
            if not selection_input:
                return None, "No input provided, returning to the main menu."

            # Check if the input is numeric
            if not selection_input.isdigit():
                return None, "Invalid input. Please enter a valid number."

            # Convert to integer and check if within valid range
            selection_num = int(selection_input)
            if selection_num < 1 or selection_num > max_length:
                return None, f"Invalid selection. Please choose a valid number between 1 and {max_length}."

            return selection_num - 1, None  # Return 0-based index

        def validate_confirmation_input(confirmation_input):
            """
            Validates the confirmation input (y/n).
            - Whitespace is cleaned.
            """
            confirmation_input = confirmation_input.strip().lower()

            # Only accept 'y', 'n', or blank (to go back)
            if confirmation_input not in ['y', 'n', '']:
                return None, "Invalid input. Please enter 'y' or 'n'."

            return confirmation_input, None

        try:
            # Fetch users from the database using the request_get_users method
            users_response = Functions_ui.request_get_users(sessionToken, current_username)

            if users_response and users_response['statusCode'] == 200:
                users = users_response['users']

                # Filter out the current admin account, test accounts, and super administrators
                admin_accounts = [
                    user for user in users
                    if user['username'] not in ['super_admin', 'system_admin', 'consultant']
                    and user['username'] != current_username
                    and user['user_role_id'] != 3  # Exclude super administrators
                    and user['user_role_id'] in [2, 3]  # Only include system administrators and super administrators
                ]

                # Check if there are any admin accounts available
                if not admin_accounts:
                    print("No admin accounts available for deletion.")
                    return

                # Sort by role and then by username
                admin_accounts.sort(key=lambda x: (x['user_role_id'] if x['user_role_id'] is not None else float('inf'),
                                                   x['username'] if x['username'] is not None else ''))

                # Define field widths for better alignment
                username_width = max(len(admin['username']) for admin in admin_accounts) + 2  # Adding some padding
                role_width = max(len(admin['user_role_name']) for admin in admin_accounts) + 2  # Adding some padding

                # Print header
                print(f"{'Index':<5} {'Username':<{username_width}} {'Role':<{role_width}}")
                print("-" * (5 + username_width + role_width))  # Separator line

                # Display admin accounts with formatted output
                for index, admin in enumerate(admin_accounts):
                    # Convert role_id to a friendly name
                    if admin['user_role_id'] == 2:
                        role_name = "System Administrator"
                    elif admin['user_role_id'] == 3:
                        role_name = "Super Administrator"
                    else:
                        role_name = "Unknown Role"  # Fallback if role ID is unexpected

                    print(f"{index + 1:<5} {admin['username']:<{username_width}} {role_name:<{role_width}}")

                # Loop for valid admin selection
                while True:
                    # Ask user for the index of the admin to delete
                    selection_input = safe_input(current_username, "Enter the number of the admin to delete (or press Enter to return to the main menu): ").strip()

                    # Validate the user's input
                    valid_selection, validation_error = validate_selection_input(selection_input, len(admin_accounts))

                    # Handle invalid input (keep looping if input is invalid)
                    if validation_error:
                        if not selection_input:  # If input is blank
                            print(validation_error)
                            return  # Return to main menu
                        print(validation_error)
                        continue  # Reprompt if invalid

                    # Get the ID and role of the selected admin
                    admin_id_to_delete = admin_accounts[valid_selection]['id']
                    admin_role_id = admin_accounts[valid_selection]['user_role_id']
                    admin_username = admin_accounts[valid_selection]['username']

                    # Convert role ID to a friendly name
                    if admin_role_id == 2:
                        admin_role = "System Administrator"
                    elif admin_role_id == 3:
                        admin_role = "Super Administrator"
                    else:
                        admin_role = "Unknown Role"  # Fallback if role ID is unexpected

                    # Confirmation prompt loop
                    while True:
                        confirm_input = safe_input(current_username, f"Are you sure you want to delete the {admin_role} account '{admin_username}'? (y/n): ").strip().lower()

                        # Validate confirmation input
                        valid_confirm, confirm_error = validate_confirmation_input(confirm_input)

                        if confirm_error:
                            print(confirm_error)
                            continue  # Keep looping if invalid
                        if valid_confirm == '':  # Blank input returns to main menu
                            print("Returning to main menu.")
                            return
                        if valid_confirm == 'y':
                            # Proceed with deletion
                            break  # Exit confirmation loop
                        elif valid_confirm == 'n':
                            print("Deletion cancelled.")
                            return  # Exit the function after cancellation

                    # Create the event object for deletion
                    event = {
                        "header": {
                            "token": sessionToken,
                            "permissionId": 8  # Assuming 8 is the permission ID for deleting admin
                        },
                        "body": {
                            "userId": admin_id_to_delete
                        }
                    }

                    # Call the delete_user function with the admin ID
                    response = invoke_function(event)

                    # Check the response and print the appropriate message
                    if response['statusCode'] == 200:
                        print(f"{admin_role} account '{admin_username}' deleted successfully!")  # Specify the admin role
                    else:
                        print(f"Failed to delete admin account: {response['message']}")
                    break  # Exit after deletion
            else:
                print("Failed to fetch admin accounts.")
        except Exception as e:
            print(f"An error occurred: {e}")





    @staticmethod
    def reset_consultant_password_ui(session_token, current_username):
        # Prepare the event object for fetching consultants
        event = {
            "header": {
                "token": session_token,
                "permissionId": 5,  # Permission ID for viewing users
                "userRoleId": 1  # User role ID for consultants
            }
        }

        # Get the list of consultants from the backend
        consultant_response = invoke_function(event)

        if consultant_response.get("statusCode") == 200:
            consultants = consultant_response.get("users")

            # Filter out users with specific usernames
            filtered_consultants = [
                consultant for consultant in consultants
                if consultant['username'] not in ['system_admin', 'super_admin', 'consultant']
            ]

            if not filtered_consultants:
                print("No consultant accounts available for password reset.")
                return

            print("\n--- Consultants List ---")
            for consultant in filtered_consultants:
                print(f"ID: {consultant['id']}, Username: {consultant['username']}")

            while True:
                consultant_id = safe_input(current_username, "Enter the ID of the consultant to reset password (or press Enter to cancel): ").strip()

                if not consultant_id:
                    print("No selection made, going back to main menu.")
                    return

                # Check if consultant ID exists
                consultant_exists = any(str(consultant["id"]) == consultant_id for consultant in filtered_consultants)
                if not consultant_exists:
                    print("ID doesn't exist, please choose another.")
                else:
                    break

            # Prepare the event object for resetting the password
            event = {
                "header": {"token": session_token, "permissionId": 9},
                "body": {
                    "userId": consultant_id
                }
            }

            # Call the reset password function
            response = invoke_function(event)

            if response and response.get("statusCode") != 200:
                print("Something went wrong: ", response.get("message"))
            elif response:
                print(response.get("message"))
        else:
            print("Failed to fetch consultants.")



    @staticmethod
    def modify_admin_ui(sessionToken, current_username):
        try:
            # Fetch all users from the database
            event = {
                "header": {
                    "token": sessionToken,
                    "permissionId": 5  # Permission ID for viewing users
                },
                "body": {}
            }
            users_response = invoke_function(event)

            if users_response.get("statusCode") == 200:
                users = users_response.get("users")

                # Filter to get only admin accounts excluding 'system_admin', 'super_admin', 'consultant'
                admin_accounts = [
                    user for user in users
                    if user['user_role_id'] in [2, 3] and user['username'] not in ['system_admin', 'super_admin', 'consultant']
                ]

                if not admin_accounts:
                    print("No admin accounts available for modification.")
                    return None

                # Display admin accounts
                print("\n--- Admin Accounts ---")
                for index, admin in enumerate(admin_accounts):
                    role_name = "System Administrator" if admin['user_role_id'] == 2 else "Super Administrator"
                    print(f"{index + 1}. Username: {admin['username']} | Role: {role_name}")

                # Get user selection
                selection_input = safe_input(current_username, "Enter the number of the admin to modify (or leave blank to go back): ").strip()
                if not selection_input:
                    print("No selection made. Going back to the main menu.")
                    return None

                try:
                    selection = int(selection_input) - 1
                    if selection < 0 or selection >= len(admin_accounts):
                        print("Invalid selection. Going back to the main menu.")
                        return None
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    return None

                selected_admin = admin_accounts[selection]
                admin_id = selected_admin['id']

                print(f"Modifying account for {selected_admin['username']}")

                # Username validation with two attempts
                for attempt in range(2):
                    username = safe_input(current_username, "Enter new username (leave blank to keep current): ").strip().lower()
                    if not username:  # Keep current if left blank
                        username = selected_admin['username']
                        break
                    is_valid, message = Functions_ui.validate_username(username)
                    if is_valid:
                        break
                    else:
                        print(message)
                        if attempt == 1:
                            print("Too many invalid attempts. Keeping current username.")
                            username = selected_admin['username']
                            break

                # Password validation with two attempts
                for attempt in range(2):
                    password = safe_input(current_username, "Enter new password (leave blank to keep current): ").strip()
                    if not password:  # If input is blank, keep current password
                        password = None
                        break
                    is_valid, message = Functions_ui.validate_password(password)
                    if is_valid:
                        break
                    else:
                        print(message)
                        if attempt == 1:
                            print("Too many invalid attempts. Keeping current password.")
                            password = None
                            break

                # Always ask for role change but keep current role if left blank
                new_role_input = safe_input(current_username, "Enter the number of the new role (1 for System Administrator, 2 for Super Administrator, leave blank to keep current): ").strip()
                if not new_role_input:
                    new_role_id = selected_admin['user_role_id']  # Keep current role
                elif new_role_input == '1':
                    new_role_id = 2  # System Administrator role
                elif new_role_input == '2':
                    new_role_id = 3  # Super Administrator role
                else:
                    print("Invalid role selection. Keeping current role.")
                    new_role_id = selected_admin['user_role_id']  # Keep current role

                # Check if no changes were made
                if (username == selected_admin['username'] and
                        password is None and
                        new_role_id == selected_admin['user_role_id']):
                    print("No changes made. Going back to the main menu.")
                    return None

                # Prepare event for modifying the user
                event = {
                    "header": {"token": sessionToken, "permissionId": 7},
                    "body": {
                        "userId": admin_id,
                        "username": username,
                        "user_role_id": new_role_id
                    }
                }

                if password:
                    event['body']['password'] = password

                # Call the edit_user function to modify the admin details
                response = invoke_function(event)

                if response and response.get("statusCode") == 200:
                    print("Admin updated successfully!")
                else:
                    print(f"Failed to update admin: {response.get('message')}")

        except Exception as e:
            print(f"An error occurred: {e}")





    @staticmethod
    def update_own_password(session_token, current_username):
        # Vraag gebruiker om wachtwoord en valideer
        while True:
            password = safe_input(current_username,
                                  "Enter new password (leave blank to return to main menu): ").strip()
            if not password:  # Check if the input is left blank
                print("Password not provided, going back to the main menu.")
                return  # Exit and return to the main menu
            is_valid, message = Functions_ui.validate_password(password)
            if is_valid:
                break
            else:
                print(message)

        # Prepare the event object for updating the password
        event = {
            "header": {"token": session_token, "permissionId": 1},
            "body": {"password": password}
        }

        # Call the update password function
        response = invoke_function(event)

        print(response.get("message"))

        return response

    @staticmethod
    def reset_admin_password_ui(sessionToken, current_username):
        # Prepare the event object for fetching admins
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 5,  # Permission ID for viewing users
                "userRoleId": 2  # User role ID for system admins
            }
        }

        # Get the list of admins from the backend
        admin_response = invoke_function(event)

        if admin_response.get("statusCode") == 200:
            admins = admin_response.get("users")

            # Filter out users with specific usernames (system_admin, super_admin, consultant)
            filtered_admins = [
                admin for admin in admins
                if admin['username'] not in ['system_admin', 'super_admin', 'consultant']
            ]

            if not filtered_admins:
                print("No admin accounts available for password reset.")
                return

            print("\n--- System Administrators List ---")
            for admin in filtered_admins:
                print(f"ID: {admin['id']}, Username: {admin['username']}")

            while True:
                admin_id = safe_input(current_username, "Enter the ID of the admin to reset password (or press Enter to cancel): ").strip()

                if not admin_id:
                    print("No selection made, going back to main menu.")
                    return

                # Check if admin ID exists in the filtered list
                admin_exists = any(str(admin["id"]) == admin_id for admin in filtered_admins)
                if not admin_exists:
                    print("ID doesn't exist, please choose another.")
                else:
                    break

            # Prepare the event object for resetting the password
            event = {
                "header": {"token": sessionToken, "permissionId": 16},  # Assuming 16 is the permission ID for resetting password
                "body": {
                    "userId": admin_id
                }
            }

            # Call the reset password function
            response = invoke_function(event)

            if response and response.get("statusCode") != 200:
                print("Something went wrong: ", response.get("message"))
            elif response:
                print(response.get("message"))
        else:
            print("Failed to fetch admin accounts.")


    @staticmethod
    def search_member_ui(sessionToken, current_username):
        def validate_search_query(query):
            """
            Validate the search query to ensure:
            - It only contains alphanumeric characters, spaces, '@' and '.'
            - '@' and '.' must not appear consecutively more than once.
            - Clean excess whitespace.
            """
            # Clean up whitespace
            cleaned_query = ' '.join(query.split()).strip()

            # Validate using a regular expression
            # Whitelist: alphanumeric characters, spaces, '@', and '.'
            # Ensure no consecutive '@' or '.' symbols
            if not re.match(r"^[a-zA-Z0-9@.\s]+$", cleaned_query) or re.search(r"[@.]{2,}", cleaned_query):
                raise ValueError("Invalid input. Only alphanumeric characters, spaces, '@' and '.' are allowed, and no consecutive '@' or '.' symbols.")
        
            return cleaned_query

        # Fetch all members to check if the database has any members
        event = {
            "header": {
                "token": sessionToken,
                "permissionId": 4,  # Assuming permissionId 4 is for fetching members
            },
            "body": {}  # Empty body to fetch all members
        }

        response = invoke_function(event)

        if response['statusCode'] == 200:
            all_members = response['members']
            if not all_members:
                print("No members found in the system.")
                return  # Exit the function if no members are found

        # Ask user for the search query after confirming that members exist
        while True:
            search_query = safe_input(current_username, "Search for a member (or press enter to view all): ").strip()

            if not search_query:
                # If no search query is provided, fetch all members
                break
            try:
                search_query = validate_search_query(search_query)
                # If validation is successful, break out of the loop
                break
            except ValueError as e:
                print(e)  # Print validation error and reprompt the user

        # Prepare the event object for the search query or fetch all members if no query
        if search_query:
            event = {
                "header": {
                    "token": sessionToken,
                    "permissionId": 4,
                    "searchQuery": search_query
                }
            }
        else:
            # Fetch all members if no search query is provided
            event = {
                "header": {
                    "token": sessionToken,
                    "permissionId": 4,
                },
                "body": {}  # Empty body to fetch all members
            }

        # Call the search member function
        response = invoke_function(event)

        if response['statusCode'] == 200:
            members = response['members']
            if members:
                # Define column headers and widths based on maximum lengths
                headers = ["ID", "Name", "Email", "Phone", "Address", "Age", "Gender", "Weight", "Date Joined"]
                widths = [
                    13,  # ID
                    2 * 15 + 4,  # Name (first and last name combined with a space)
                    27,  # Email
                    17,  # Phone
                    24,  # Address
                    6,  # Age
                    17,  # Gender
                    9,  # Weight
                    15  # Date Joined
                ]

                # Print the header row
                header_row = "".join(f"{headers[i]:<{widths[i]}}" for i in range(len(headers)))
                print(header_row)
                print("-" * sum(widths))  # Print a separator line

                # Loop through each member and print the details
                for member in members:
                    name = f"{member['first_name']} {member['last_name']}"
                    row = (
                        f"{str(member['id']):<{widths[0]}}"
                        f"{name:<{widths[1]}}"
                        f"{(member['email_address'] or ''):<{widths[2]}}"
                        f"{(member['mobile_phone'] or ''):<{widths[3]}}"
                        f"{(member['address'] or ''):<{widths[4]}}"
                        f"{(str(member['age']) or ''):<{widths[5]}}"
                        f"{(member['gender'] or ''):<{widths[6]}}"
                        f"{(str(member['weight']) or ''):<{widths[7]}}"
                        f"{(member['created_on'] or ''):<{widths[8]}}"
                    )
                    print(row)
            else:
                print("No members found matching the search query.")
        else:
            print("Failed to search for members.")



   


    @staticmethod
    def validate_username(username):
        # Clean whitespace and check for null-byte characters
        username = username.strip().lower()  # Clean leading/trailing whitespace

        # Check length between 8 and 10 characters
        if len(username) < 8 or len(username) > 10:
            return False, "Username must be between 8 and 10 characters long."

        # Username must start with a letter or underscore
        if not (username[0].isalpha() or username[0] == "_"):
            return False, "Username must start with a letter or underscore."

        # Username can only contain letters, numbers, underscores, apostrophes, and periods (whitelisting)
        for char in username:
            if not (char.isalnum() or char in ["_", "'", "."]):
                return False, "Username can only contain letters, numbers, underscores, apostrophes, or periods."

        # Check if the username contains multiple consecutive special characters (optional stricter rule)
        if any(char1 == char2 and char1 in "_'." for char1, char2 in zip(username, username[1:])):
            return False, "Username contains consecutive special characters."

        return True, "Valid username."

    @staticmethod
    def validate_password(password):
        # Clean whitespace and check for null-byte characters
        password = password.strip()  # Clean leading/trailing whitespace
        # Check length between 12 and 30 characters
        if len(password) < 12 or len(password) > 30:
            return False, "Password must be between 12 and 30 characters long."

        # Password must contain at least one lowercase letter
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter."

        # Password must contain at least one uppercase letter
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter."

        # Password must contain at least one digit
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit."

        # Password must contain at least one special character from the allowed list (whitelisting)
        special_characters = "!@#$%^&*()_+=-`[]{}|;:'\",.<>?/~"
        if not any(char in special_characters for char in password):
            return False, "Password must contain at least one special character."

        # Additional check: ensure password doesn't contain disallowed characters
        allowed_characters = string.ascii_letters + string.digits + special_characters
        for char in password:
            if char not in allowed_characters:
                return False, "Password contains invalid characters."

        return True, "Valid password."




