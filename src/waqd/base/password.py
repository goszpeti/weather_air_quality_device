import json
from pathlib import Path
from threading import Lock
import bcrypt
import os
import waqd
import random
import string
from waqd.base.logger import Logger


DEFAULT_USERNAME = "default_waqd_user"

class UserFileDB():
    lock = Lock()  # lock for file
    encoding = 'UTF-8'

    def __init__(self, default_pw="") -> None:
        self.__pw_file_path = Path(waqd.user_config_dir / "user_db.json")
        # create Settings ini file, if not available for first start
        if not self.__pw_file_path.is_file():
            os.makedirs(self.__pw_file_path.parent, exist_ok=True)
            self.__pw_file_path.touch()
            self.__pw_file_path.write_text("{}")
            self.write_entry(DEFAULT_USERNAME, default_pw)
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
