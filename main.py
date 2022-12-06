import argparse
from datetime import datetime, date, time, timedelta

import log_in
from config import Config
from room import Room, RoomManager, book_room


def print_room(room: Room, datetime_obj: datetime):
    print(str(room_id).rjust(2), ":", room.name, room.room_next_occupied_time_slot(datetime_obj), "|",
          room.description)


if __name__ == "__main__":
    open("config.pickle", 'a').close()
    open("rooms.pickle", 'a').close()
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-v", "--verbose", default=False, action="store_true")
    argparser.add_argument("-u", "--user", required=True, type=str)
    argparser.add_argument("-p", "--password", required=True, type=str)
    argparser.add_argument("-i", "--update_interval", default=7, type=int)
    argparser.add_argument("-b", "--booking_interval", default=7, type=int)
    argparser.add_argument("-d", "--date", default=date.today(), type=date.fromisoformat)
    argparser.add_argument("-t", "--time", default=datetime.now().time(), type=time.fromisoformat)
    argparser.add_argument("-m", "--min_seats", default=4, type=int)

    args = argparser.parse_args()
    cfg = Config(args.user, args.password, args.verbose, args.update_interval)
    Config.load_persist()
    if not cfg.check_persist():
        print("Config file broken, rebuilding...")
        cfg.rebuild_persist()
        log_in.try_login(cfg)

    room_manager = RoomManager.from_pickle(cfg)
    if datetime.now() > room_manager.last_updated + timedelta(days=cfg.room_update_interval)\
            or not room_manager.room_dict:
        print("Updating room data...")
        room_manager.update_rooms()
        print("Success")

    #
    booking_datetime_obj = datetime.combine(args.date, args.time) + timedelta(days=args.booking_interval)
    room_manager.update_events(args.date.isoformat())
    room_dict = room_manager.room_dict
    print("Verfügbare Räume:")
    for room_id, room in room_dict.items():
        if room.time_slot_not_occupied(booking_datetime_obj) and int(room.min_seats) >= args.min_seats:
            print_room(room, booking_datetime_obj)

    chosen_room: Room
    chosen_room = max(
        filter(
            lambda room: room.time_slot_not_occupied(booking_datetime_obj) and int(room.min_seats) >= args.min_seats,
            room_dict.values()),
        key=lambda room: room.room_next_occupied_time_slot(booking_datetime_obj)
    )
    print("Ausgewählter Raum:")
    print_room(chosen_room, booking_datetime_obj)
    date = booking_datetime_obj.date().isoformat()
    print("Datum:", date)
    start_time = booking_datetime_obj.strftime("%H:%M")
    print("Startzeit:", start_time)
    end_time = min(
        chosen_room.room_next_occupied_time_slot(booking_datetime_obj), booking_datetime_obj + timedelta(hours=4)
    ).strftime("%H:%M")
    print("Endzeit:", end_time)
    response_content = book_room(chosen_room, start_time, end_time, date, cfg)
    print(response_content)
