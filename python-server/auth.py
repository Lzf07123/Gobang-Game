import os
import re
import secrets
import bcrypt
import jwt
import time
import mysql.connector
from db import execute_query, set_user_session

_USERNAME_RE = re.compile(r'^[\w一-鿿]{2,20}$')

_JWT_SECRET = os.getenv('JWT_SECRET', '')
if not _JWT_SECRET or _JWT_SECRET == 'your_jwt_secret_key_change_me':
    _JWT_SECRET = secrets.token_hex(32)
    print("⚠ JWT_SECRET 未设置或使用默认值，已自动生成临时密钥（重启后失效）")
    print("   请将以下密钥写入 python_server/.env 中的 JWT_SECRET= 使其持久化：")
    print(f"   JWT_SECRET={_JWT_SECRET}")
_JWT_EXPIRY = 7200  # 2 hours


def _hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _make_token(username, session_id):
    payload = {
        'username': username,
        'session_id': session_id,
        'exp': int(time.time()) + _JWT_EXPIRY,
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm='HS256')


def verify_token(token):
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=['HS256'])
        return payload['username'], payload.get('session_id', '')
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None


def register(username, password):
    if not username or not _USERNAME_RE.match(username):
        return False, "用户名仅支持中英文、数字、下划线，2-20个字符"
    if len(password) < 6:
        return False, "密码长度至少6位"

    existing = execute_query(
        "SELECT id FROM users WHERE username = %s", (username,)
    )
    if existing:
        return False, "用户名已存在"

    pw_hash = _hash_password(password)
    try:
        execute_query(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, pw_hash), fetch=False
        )
    except mysql.connector.IntegrityError:
        return False, "用户名已存在"
    return True, None


def login(username, password):
    rows = execute_query(
        "SELECT password_hash FROM users WHERE username = %s", (username,)
    )
    if not rows:
        return False, "用户名或密码错误"

    if not _check_password(password, rows[0]['password_hash']):
        return False, "用户名或密码错误"

    session_id = secrets.token_hex(16)
    set_user_session(username, session_id)

    token = _make_token(username, session_id)
    return True, token
