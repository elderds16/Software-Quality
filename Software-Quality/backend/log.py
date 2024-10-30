import os
import json
import logging
import datetime

class Log:
    """
    Log class to handle logging of activities
    """
    logs_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    log_file = os.path.join(logs_directory, 'system_log.enc')
    key_file = os.path.join(logs_directory, 'secret.key')

    def __init__(self):
        self.suspicious_activities = []

        # Ensure the logs directory exists
        if not os.path.exists(self.logs_directory):
            os.makedirs(self.logs_directory)

        # Key management
        if not os.path.exists(self.key_file):
            self.key = os.urandom(16)  # Generate a random 16-byte key
            with open(self.key_file, 'wb') as key_file:
                key_file.write(self.key)
        else:
            with open(self.key_file, 'rb') as key_file:
                self.key = key_file.read()

        # Log file management
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'wb') as log_file:
                log_file.write(self.encrypt(b'[]'))

        # Set up the logger
        logging.basicConfig(level=logging.INFO, format='%(message)s')
        self.logger = logging.getLogger('ActivityLogger')

    def log_activity(self, username, description, additional_info, suspicious=False):
        # check if any input is None or empty, if so convert it to a string
        username = username if username else ''
        description = description if description else ''
        additional_info = additional_info if additional_info else ''

        log_entry = {
            "id": self._generate_id(),
            "date": datetime.datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.datetime.now().strftime('%H:%M:%S'),
            "username": username,
            "description": description,
            "additional_info": additional_info,
            "suspicious": suspicious
        }

        logs = self._read_logs()
        logs.append(log_entry)
        self._write_logs(logs)

        if suspicious:
            self.suspicious_activities.append(log_entry)

    def get_unread_suspicious_activities(self):
        unread_activities = [activity for activity in self.suspicious_activities]
        self.suspicious_activities = []
        return unread_activities

    def read_all_logs(self):
        # Read and decrypt logs
        with open(self.log_file, 'rb') as log_file:
            encrypted_data = log_file.read()
        decrypted_data = self.decrypt(encrypted_data).decode('utf-8')
        logs = json.loads(decrypted_data)
        return logs


    def _generate_id(self):
        logs = self._read_logs()
        if logs:
            return logs[-1]['id'] + 1
        else:
            return 1

    def _read_logs(self):
        with open(self.log_file, 'rb') as log_file:
            encrypted_data = log_file.read()
        decrypted_data = self.decrypt(encrypted_data).decode('utf-8')
        return json.loads(decrypted_data)

    def _write_logs(self, logs):
        data = json.dumps(logs).encode('utf-8')
        encrypted_data = self.encrypt(data)
        with open(self.log_file, 'wb') as log_file:
            log_file.write(encrypted_data)

    def encrypt(self, data):
        return bytearray([data[i] ^ self.key[i % len(self.key)] for i in range(len(data))])

    def decrypt(self, data):
        return bytearray([data[i] ^ self.key[i % len(self.key)] for i in range(len(data))])

    def warning(self, message):
        self.logger.warning(message)


def read_logs(event):
    """
    Read all logs and return them
    :param event: which is the event dict
    :return: the logs dict
    """
    return {"statusCode": 200, "message": "Successfully retrieved logs", "logs": Log().read_all_logs()}
