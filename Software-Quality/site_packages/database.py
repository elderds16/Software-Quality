import sqlite3
import os


class Database:
    """
    Database context manager to handle database connections
    """

    _connection = None  # Class variable to store the connection

    def __init__(self):
        # Initialize the database path
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../backend/UM.db")

    def __enter__(self):
        # Connect to the database at the hardcoded path
        self.connection = sqlite3.connect(self.db_path)
        Database._connection = self.connection  # Store the connection for later use
        return self.connection, self.connection.cursor()

    def __exit__(self, exit_type, value, traceback):
        if self.connection:
            self.connection.commit()  # Commit any changes
            self.connection.close()  # Close the connection
            Database._connection = None  # Clear the stored connection

    @classmethod
    def close_all_connections(cls):
        """
        Close the stored connection if it exists
        :return:
        """
        if cls._connection:
            cls._connection.close()
            cls._connection = None  # Clear the stored connection
