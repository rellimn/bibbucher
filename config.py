import sys
from typing import Dict, Union

import pickle


class Config:
    BASE_DICT = {"user": {"headers": {"X-XSRF-TOKEN": ""}, "cookies": {"zeitwart_session": ""}, "user_id": 0}}

    ROOM_LIST = [1, 3, 2, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28,
                 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 41, 42, 43, 44, 45]

    persist: Dict[str, Union[str, int, Dict]]
    persist = {}

    def __init__(self, user: str, password: str, verbose: bool, room_update_interval: int):
        self.user = user
        self.password = password
        self.verbose = verbose
        self.room_update_interval = room_update_interval

    def __str__(self):
        return f"{self.user} {self.password}{' VERBOSE' if self.verbose else ''}"

    def get_from_persist(self, key: str):
        return Config.persist.get(self.user).get(key)

    @classmethod
    def load_persist(cls):
        try:
            f = open("config.pickle", "rb")
            cls.persist = pickle.load(f)
        except (EOFError, FileNotFoundError):
            print("Error loading persist", file=sys.stderr)
        finally:
            f.close()

    def check_persist(self):
        return Config.persist.get(self.user)

    @classmethod
    def save_persist(cls):
        with open('config.pickle', 'wb') as f:
            pickle.dump(cls.persist, f)

    @classmethod
    def persist_indiv_data(cls, user: str,
                           x_xsrf_token: str, zeitwart_session: str, user_id: int):
        cls.persist[user] = {
            "headers": {"X-XSRF-TOKEN": x_xsrf_token},
            "cookies": {"zeitwart_session": zeitwart_session},
            "user_id": user_id
        }
        cls.save_persist()

    @classmethod
    def rebuild_persist(cls):
        cls.persist = cls.BASE_DICT
        cls.save_persist()


def get_type(value):
    if isinstance(value, dict):
        return {key: get_type(value[key]) for key in value}
    else:
        return str(type(value))


if __name__ == "__main__":
    Config.load_persist()
    print(Config.check_persist())
