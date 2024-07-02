from functools import wraps
from flask import request, jsonify
import os

def admin_api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-KEY')
        expected_api_key = os.getenv('ADMIN_API_KEY')
        if not api_key or api_key != expected_api_key:
            return jsonify({'message': 'Unauthorized access'}), 401
        return f(*args, **kwargs)
    return decorated_function