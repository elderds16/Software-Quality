import re

from backend.log import Log

MAX_NAME_LENGTH = 15
MAX_EMAIL_LENGTH = 25
MAX_ADDRESS_LENGTH = 20
MAX_GENDER_LENGTH = 15
MAX_WEIGHT_LENGTH = 4

def safe_input(_username, prompt):
    """
    Get user input and check for suspicious patterns
    :param _username: which is the username of the user
    :param prompt: which is the message to display to the user
    :return:
    """
    user_input = input(prompt)
    check_suspicious_input(_username, user_input)
    return user_input


def check_suspicious_input(_username, user_input):
    """
    Check for suspicious patterns in user input and log them as activities if found
    :param _username: which is the username of the user
    :param user_input: which is the input to check
    :return:
    """
    violations = []
    max_log_input_length = 250  # Maximum length of input text to be logged

    # 1. Check for SQL Injection patterns
    sql_patterns = [
        r"(\b(OR|AND)\b\s+[^\s]+\s*=\s*[^\s]+)",  # OR/AND-based injections
        r"(--|#|\/\*|\*\/)",  # SQL comments or block comments
        r"(\bSELECT\b|\bDROP\b|\bDELETE\b|\bINSERT\b|\bUPDATE\b)",  # SQL keywords
        r"(';|\";|';--|\";--|';#|\";#)"  # Ending the input with SQL comments or semicolon
    ]
    for pattern in sql_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            violations.append("SQL Injection attempt detected")

    # 2. Check for Command Injection patterns
    command_patterns = [
        r"(\|\||&&|\$\(.*\)|`.*`|;)",  # Command chaining or execution symbols
        r"(\brm\b|\bshutdown\b|\bdel\b|\breboot\b)",  # Dangerous commands
    ]
    for pattern in command_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            violations.append("Command Injection attempt detected")

    # 3. Check for XSS patterns (in case the input is used in a UI context)
    xss_patterns = [
        r"(<script.*?>.*?</script.*?>)",  # Script tags
        r"(<.*?on\w+=.*?>)",  # Inline event handlers (e.g., onerror, onclick)
        r"(\"<|'>|<img\s+src\s*=.*onerror=.*>)"  # Image tags with onerror attribute
    ]
    for pattern in xss_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            violations.append("XSS attempt detected")

    # 4. Check for Buffer Overflow or excessively long input
    if len(user_input) > 255:  # Set a reasonable limit for input length
        violations.append("Excessively long input detected (possible Buffer Overflow)")

    # 5. Check for Path Traversal
    path_traversal_patterns = [
        r"(\.\./|\.\.\\|\/etc\/|C:\\windows\\)",  # Relative paths or system paths
    ]
    for pattern in path_traversal_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            violations.append("Path Traversal attempt detected")

    # 6. Check for encoded input or obfuscation
    encoded_patterns = [
        r"(%[0-9a-fA-F]{2})",  # URL encoded characters
        r"(base64\s*=\s*['\"].*?['\"])"  # Base64-encoded content
    ]
    for pattern in encoded_patterns:
        if re.search(pattern, user_input, re.IGNORECASE):
            violations.append("Encoded or obfuscated input detected")

    # 7. Check for invalid data types (basic validation)
    if user_input.isdigit() and int(user_input) < 0:
        violations.append("Negative value in numeric field detected")

    # 8. Check for null bytes (used in some attacks)
    try:
        user_input_bytes = user_input.encode("utf-8").decode('unicode_escape')
        if b"\x00" in user_input_bytes.encode() or b"\0" in user_input_bytes.encode():
            violations.append("Null byte detected")
    except UnicodeDecodeError:
        violations.append("Invalid escape sequence detected in input")

    # If any violations were found, log them as suspicious activities
    if violations:
        # Prepare the input for logging
        if len(user_input) > max_log_input_length:
            truncated_input = user_input[:max_log_input_length] + "..."  # Log only part of the input
        else:
            truncated_input = user_input

        Log().log_activity(
            username=_username,
            description="Suspicious input detected",
            additional_info=f"Violations: {', '.join(violations)} | Input: {truncated_input}",
            suspicious=True
        )

        # if not user id 3, abort the program
        if _username != "super_admin":
            print("Error: Your session has been terminated for security reasons. Please contact support if you believe this is an error.")
            exit(1)


def is_name_valid(name):
    if len(name) <= MAX_NAME_LENGTH and re.match(r'^[a-zA-Z\s]+$', name):
        return True
    else:
        return False


def is_email_valid(email_address):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if re.match(email_regex, email_address) and len(email_address) <= MAX_EMAIL_LENGTH:
        return True
    else:
        return False


def is_address_valid(address):
    if len(address) <= MAX_ADDRESS_LENGTH and re.match(r'^[a-zA-Z0-9\s,.-]+$', address):
        return True
    else:
        return False


def is_age_valid(age_str):
    if age_str.isdigit():
        age_str = int(age_str)
        if 18 <= age_str <= 125:
            return True
    return False


def is_weight_valid(weight_str):
    if weight_str.replace('.', '', 1).isdigit() and 0 < float(weight_str) <= 500 and len(weight_str) <= MAX_WEIGHT_LENGTH:
        return True
    else:
        return False


def is_mobile_valid(mobile_str):
    if re.match(r'^[0-9]{8}$', mobile_str):
        return True
    else:
        return False


def is_gender_valid(gender):
    if gender.lower() in ["male", "m", "female", "f", "other", "o"]:
        return True
    else:
        return False
