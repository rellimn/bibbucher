import pickle
import traceback
from datetime import datetime
from typing import Tuple, List, Dict

import requests
from bs4 import BeautifulSoup

from config import Config
from log_in import try_login, LoginError


class Room:
    last_updated = None
    room_dict = Dict[int, "Room"]

    def __init__(self, id: int, name: str, events: List[Tuple[str, str]], description: str, slug: str, floor: str,
                 min_seats: int, max_seats: int, unit: int):
        self.id = id
        self.name = name
        self.events = events
        self.description = description
        self.slug = slug
        self.floor = floor
        self.min_seats = min_seats
        self.max_seats = max_seats
        self.unit = unit

    @staticmethod
    def get_max_datetime(ref_time: datetime) -> datetime:
        return datetime.strptime(ref_time.strftime("%Y-%m-%d") + " 22:00:00", "%Y-%m-%d %H:%M:%S")

    def time_slot_not_occupied(self, ref_time: datetime) -> bool:
        return not any(map(lambda event: datetime.fromisoformat(event[0]) <= ref_time < datetime.fromisoformat(event[1]),
                           self.events))

    def room_next_occupied_time_slot(self, ref_time: datetime) -> datetime:
        max_datetime = Room.get_max_datetime(ref_time)
        return min(
            filter(lambda event_start_datetime: event_start_datetime > ref_time,
                   map(lambda event: datetime.fromisoformat(event[0]), self.events)),
            default=max_datetime)

    def add_event(self, start: str, end: str) -> None:
        self.events.append((start, end))

    def __str__(self):
        return f"{self.id}: {self.name}, {self.description}, " \
               f"{self.floor}, {self.min_seats}-{self.max_seats}, {self.events}"


class RoomManager:
    def __init__(self, cfg: Config):
        self.room_dict: Dict[int, Room]
        self.room_dict = {}
        self.last_updated = datetime.now()
        self.cfg = cfg

    def add_event_from_id(self, id: int, start: str, end: str) -> None:
        if self.room_dict.get(id):
            self.room_dict[id].add_event(start, end)

    def clear_events_from_id(self, id: int):
        self.room_dict[id].events = []

    def clear_all_events(self):
        for room_id, room in self.room_dict.items():
            self.clear_events_from_id(room_id)

    def dump_rooms(self) -> None:
        with open("rooms.pickle", "wb") as f:
            self.last_updated = datetime.now()
            pickle.dump((self.room_dict, self.last_updated), f)

    def load_rooms(self):
        with open("rooms.pickle", "wb") as f:
            room_manager_tuple = pickle.load(f)
        self.room_dict, self.last_updated = room_manager_tuple

    @classmethod
    def from_pickle(cls, cfg: Config) -> "RoomManager":
        room_manager_tuple = None
        try:
            f = open("rooms.pickle", "rb")
            room_manager_tuple = pickle.load(f)
        except (EOFError, FileNotFoundError):
            if cfg.verbose:
                traceback.print_exc()
        finally:
            f.close()
        room_manager = cls(cfg)
        if room_manager_tuple:
            room_manager.room_dict, room_manager.last_updated = room_manager_tuple
        return room_manager

    def update_rooms(self):
        url = f"https://zeitwart.hs-osnabrueck.de/api/v1/users/{self.cfg.get_from_persist('user_id')}" \
              f"/rooms?page=1&itemsPerPage=99&filter_homepage=2&columns[]=events"

        _headers = self.cfg.get_from_persist("headers").copy()
        _headers["Accept"] = "application/json"
        _headers["Origin"] = "https://zeitwart.hs-osnabrueck.de"
        response = requests.get(url,
                                cookies=self.cfg.get_from_persist("cookies"),
                                headers=_headers)
        r_title = BeautifulSoup(response.content, "html.parser").title
        if (r_title and r_title.string == "Page Expired") or response.json().get("message") == "CSRF token mismatch.":
            _headers = self.cfg.get_from_persist("headers").copy()
            _headers["Accept"] = "application/json"
            _headers["Origin"] = "https://zeitwart.hs-osnabrueck.de"
            try_login(self.cfg)
            response = requests.get(url, cookies=self.cfg.get_from_persist("cookies"), headers=_headers)

        room_dict = {}
        for x in response.json()["data"]:
            if x["id"] in Config.ROOM_LIST:
                room_dict[x["id"]] = {"id": x["id"], "name": x["name"], "slug": x["slug"],
                                      "description": x["model_attributes"]["description"]["value"],
                                      # We use .get because floor can be missing, [] would result in a KeyError exception
                                      "floor": x["model_attributes"].get("floor", {"value": None})["value"],
                                      "min_seats": x["model_attributes"]["min_seats"]["value"],
                                      "max_seats": x["model_attributes"]["max_seats"]["value"],
                                      "unit": x["units"][0]["id"]}

        room_objects = {}
        for id, room in room_dict.items():
            room_objects[id] = Room(**room, events=[])

        self.room_dict = room_objects
        self.last_updated = datetime.now()
        self.dump_rooms()

    @staticmethod
    def __request_events(date: str, cfg: Config) -> requests.Response:
        """
        :param date: Date string in format YYYY-MM-DD
        :return: Returns response object
        """
        _headers = cfg.get_from_persist("headers").copy()
        _headers["Accept"] = "application/json"
        _headers["Origin"] = "https://zeitwart.hs-osnabrueck.de"
        json_data = {
            "rooms": cfg.ROOM_LIST}

        response = requests.post('https://zeitwart.hs-osnabrueck.de/api/v1/home/filter/' + date,
                                 cookies=cfg.get_from_persist("cookies"), headers=_headers, json=json_data)
        return response

    def update_events(self, date: str) -> None:
        """
        :param date: Date in Format YYYY-MM-DD
        :type date: str
        """
        r = self.__request_events(date, self.cfg)
        r_title = BeautifulSoup(r.content, "html.parser").title
        # Log in if session expired
        if (r_title and r_title.string == "Page Expired") or r.json().get("message") == "CSRF token mismatch.":
            try:
                try_login(self.cfg)
            except LoginError:
                if self.cfg.verbose:
                    traceback.print_exc()
                raise
            r = self.__request_events(date, self.cfg)

        event_data = [{"start": x["start"], "end": x["end"], "id": x["rooms"][0]["id"]} for x in r.json()["data"]]

        self.clear_all_events()
        for event in event_data:
            self.add_event_from_id(**event)


def book_room(room: Room, start_time: str, end_time: str, date: str, cfg: Config):
    url = "https://zeitwart.hs-osnabrueck.de/api/v1/events"

    _headers = cfg.get_from_persist("headers").copy()
    _headers["Accept"] = "application/json"
    _headers["Origin"] = "https://zeitwart.hs-osnabrueck.de"
    json_data = {"name": "",
                 "start_date": date,
                 "start_time": start_time,
                 "end_date": date,
                 "end_time": end_time,
                 "room_ids": [room.id],
                 "user_ids": [cfg.get_from_persist("user_id")],
                 "unit_id": room.unit,
                 "repeat": "",
                 "repeat_until": "",
                 "options": {"personal_message": "", "send_mail_to_admin": False, "send_mail_to_users": True}
                 }
    response = requests.post(url, cookies=cfg.get_from_persist("cookies"), headers=_headers, json=json_data)
    r_title = BeautifulSoup(response.content, "html.parser").title
    if (r_title and r_title.string == "Page Expired") or response.json().get("message") == "CSRF token mismatch.":
        _headers = cfg.get_from_persist("headers").copy()
        _headers["Accept"] = "application/json"
        _headers["Origin"] = "https://zeitwart.hs-osnabrueck.de"
        try_login(cfg)
        response = requests.post(url, cookies=cfg.get_from_persist("cookies"), headers=_headers, json=json_data)

    return response.content
