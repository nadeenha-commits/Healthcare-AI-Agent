def ok(data=None):
    return {'status': 'ok', 'data': data}


def error(message):
    return {'status': 'error', 'message': message}

