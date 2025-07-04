import python.db as db
from python.classes.musician import Musician
from python.classes.event import Event

from dotenv import load_dotenv

from python.db import get_constraints

load_dotenv()

try:
    print("Database reset...", db.reset(allow_fail=True))
    print("Database init...", db.init())
except Exception as e:
    print(e)
    pass

db.add_user("1234", "toto@titi.com",  "fise_1a_g1")
musician = Musician(id="1234")

assert(musician.id == "1234")
assert(musician.mail == "toto@titi.com")
assert(musician.group == "fise_1a_g1")

db.add_puncutal_constraint("1234", "01-01-2025", "18:30", "19:30")

musician = Musician(id="1234")
event = Event(db.ics_to_unixepoch("20250101T183000Z"), db.ics_to_unixepoch("20250101T193000Z"))

assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)
