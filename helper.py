from functools import wraps
import json
from flask import jsonify, make_response


def make_simple_json_response(body, status_code=200):
    resp = make_response(json.dumps(body))
    resp.status_code = status_code
    resp.mimetype = 'application/json'

    return resp

def json_view(func):
    @wraps(func)
    def nufun(*args, **kwargs):
        data, status = func(*args, **kwargs)
        return jsonify(data=data, status=status)
    return nufun


def json_fail(message):
    return {"message": message}, "FAIL"

def json_ok(data):
    return data, "OK"