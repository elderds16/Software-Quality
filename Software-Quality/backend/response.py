from backend.log import Log


def CustomResponse(statusCode, username, message, additional_information, suspicious):
    """
    Log the activity and return a custom response
    :param statusCode: which is the status code of the response
    :param username: which is the username of the user
    :param message: which is the message to return
    :param additional_information: which is additional information to log
    :param suspicious: which is a boolean indicating if the activity is suspicious
    :return: the custom response dict with status code and message
    """

    log = Log()
    log.log_activity(username, message, additional_information, suspicious)
    return {"statusCode": statusCode, "message": message}
