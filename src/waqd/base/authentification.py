import json
from pathlib import Path
from threading import Lock
from typing import Dict
import bcrypt
import os
import waqd
import re
import string
from waqd.base.file_logger import Logger


DEFAULT_USERNAME = "default_waqd_user"


def validate_username(username):
    """ Pattern: 5 to 25 alphanumerics (case insensitive) with _ - and . """
    regex = "^[a-zA-Z0-9_.-]{5,25}"
    match = bool(re.fullmatch(regex, username))
    return match


def validate_password(password):
    """ Pattern: min 6 alphanumerics (one upper one lower case), 1 number, 1 special char """
    regex = "^.*(?=.{6,})(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!+\-*&$%&? \"]).*$"
    match = bool(re.fullmatch(regex, password))
    return match

class UserAuth():
    lock = Lock()  # lock for file
    encoding = 'UTF-8'

    def __init__(self, default_pw="") -> None:
        self.__pw_file_path = Path(waqd.user_config_dir / "user_db.json")
        # create Settings ini file, if not available for first start
        if not self.__pw_file_path.is_file():
            os.makedirs(self.__pw_file_path.parent, exist_ok=True)
            self.__pw_file_path.touch()
            self.__pw_file_path.write_text("{}")
            Logger().warning('User-DB: Creating user database file')
            self.__user_db = {} # init empty
            self.set_password(DEFAULT_USERNAME, default_pw)
        with open(self.__pw_file_path, "r") as fp:
            self.__user_db: Dict[str, Dict[str, str]] = json.load(fp)

    def change_user_name(self, old_username: str, new_username: str):
        if not new_username:
            return False
        entry = self.__user_db.pop(old_username)
        if not entry:
            return False
        self.__user_db.update({new_username: entry})
        with self.lock:
            with open(self.__pw_file_path, "w") as fp:
                json.dump(self.__user_db, fp)
        return True

    def set_password(self, username: str, password: str):
        # Hash a password for the first time, with a randomly-generated salt
        salt = bcrypt.gensalt(12)
        hashed_pw = bcrypt.hashpw(password.encode(self.encoding), salt)
        assert bcrypt.checkpw(password.encode(self.encoding), hashed_pw)
        user_entry = {"pw": hashed_pw.decode(self.encoding)}
        with self.lock:
            self.__user_db.update({username: user_entry})
            with open(self.__pw_file_path, "w") as fp:
                json.dump(self.__user_db, fp)

    def get_entry(self, username: str):
            return self.__user_db.get(username, None)

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
