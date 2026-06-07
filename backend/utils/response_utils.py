def success_response(data=None, message="Success"):
    return {
        "success": True,
        "message": message,
        "data": data
    }


def error_response(message="Something went wrong", status_code=400):
    return {
        "success": False,
        "message": message,
        "status_code": status_code
    }