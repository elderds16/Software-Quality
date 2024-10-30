from backend.database_manager import DatabaseManger
from frontend.userinterface import UserInterface


def launch():
    DatabaseManger().initialize_database()
    ui = UserInterface()  # Create an instance of UserInterface
    ui.loginForm()  # Start the login procedure
    ui.display_main_menu()  # Show the main menu after logging in


launch()
