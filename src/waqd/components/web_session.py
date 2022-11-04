import base64
import hashlib
import hmac
import json
import logging
import os
import random
import string
import time
from pathlib import Path
from threading import Lock

import bcrypt
import waqd
from bottle import request, response
from waqd.base.logger import Logger

DEFAULT_USERNAME = "default_waqd_user"

def create_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for i in range(length))
    return password
class WAQDSession(dict):

    encoding = 'UTF-8'

    def __init__(self, secret, key='session.id', **params):
        self.secret = secret
        self.key = key
        self.params = params
        self.store = {}

    def save(self, set_cookie):
        if set(self.store.items()) ^ set(self.items()):
            value = dict(self.items())
            value = json.dumps(value, indent=None, separators=(',', ':'))
            value = self.encrypt(value)
            if not isinstance(value, str):
                value = value.encode(self.encoding)
            set_cookie(self.key, value, **self.params)

    def load(self, cookies, **kwargs):
        value = cookies.get(self.key, None)
        if value is None:
            return False
        if not (json_data := self.decrypt(value)):
            return False
        data = json.loads(json_data)
        if not isinstance(data, dict):
            return False
        self.store = data
        self.update(self.store)

    def create_signature(self, value, timestamp):
        h = hmac.new(self.secret.encode(), digestmod=hashlib.sha1)
        h.update(timestamp)
        h.update(value)
        return h.hexdigest()

    def encrypt(self, value):
        timestamp = str(int(time.time())).encode()
        value = base64.b64encode(value.encode(self.encoding))
        signature = self.create_signature(value, timestamp)
        return "|".join([value.decode(self.encoding), timestamp.decode(self.encoding), signature])

    def decrypt(self, value):
        value, timestamp, signature = value.split("|")
        check = self.create_signature(value.encode(self.encoding), timestamp.encode())
        if check != signature:
            return None
        return base64.b64decode(value).decode(self.encoding)


class LoginPlugin(object):

    name = 'session'
    api = 2

    def __init__(self):
        self.secret = None
        self.app = None
        self.user_loader = None

    def setup(self, app):
        if 'SECRET_KEY' not in app.config:
            raise ValueError('SECRET_KEY should be set for use the Session plugin')
        self.secret = app.config['SECRET_KEY']

    def create_session(self):
        return WAQDSession(self.secret)

    def apply(self, callback, route):
        def wrapper(*args, **kwargs):
            session = self.create_session()
            request.environ['session'] = session
            session.load(request.cookies)
            logging.debug('Started: %s', session)
            result = callback(*args, **kwargs)
            logging.debug('Ended: %s', session)
            session.save(response.set_cookie)
            return result
        return wrapper

    def load_user(self, func):
        self.user_loader = func

    def get_user(self):
        session = request.environ['session']
        user_id = session.get('user_id')
        if not user_id:
            return None
        return user_id

    @staticmethod
    def login_user(user_id):
        session = request.environ['session']
        session['user_id'] = user_id
        session.save(response.set_cookie)

    @staticmethod
    def logout_user():
        session = request.environ['session']
        session.pop('user_id', None)
        session.save(response.set_cookie)

class UserFileDB():
    lock = Lock()  # lock for file
    encoding = 'UTF-8'

    def __init__(self) -> None:
        self.__pw_file_path = Path(waqd.user_config_dir / "user_db.json")
        # create Settings ini file, if not available for first start
        if not self.__pw_file_path.is_file():
            os.makedirs(self.__pw_file_path.parent, exist_ok=True)
            self.__pw_file_path.touch()
            self.__pw_file_path.write_text("{}")
            self.write_entry(DEFAULT_USERNAME, create_password(8))
            Logger().warning('User-DB: Creating user database file')

    def write_entry(self, username: str, password: str):
        # Hash a password for the first time, with a randomly-generated salt
        salt = bcrypt.gensalt(12)
        hashed = bcrypt.hashpw(password.encode(self.encoding), salt)
        user_entry = {"pw": hashed.decode(self.encoding)}
        with self.lock:
            entries = {}
            with open(self.__pw_file_path, "r") as fp:
                entries = json.load(fp)
            with open(self.__pw_file_path, "w") as fp:
                entries.update({username: user_entry})
                json.dump(entries, fp)

    def get_entry(self, username):
        with self.lock:
            with open(self.__pw_file_path, "r") as fp:
                entries = json.load(fp)
                return entries.get(username, None)

    def check_login(self, username: str, password: str):
        # Check that an unhashed password matches one that has previously been
        # hashed
        entry = self.get_entry(username)
        if not entry:
            return False
        hashed_pw = entry.get("pw", None)
        if not hashed_pw:
            return False
        if bcrypt.checkpw(password.encode(self.encoding), 
                          hashed_pw.encode(self.encoding)):
            return True
        return False
