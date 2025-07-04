import python.db as db
import python.tools as tools
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

event = Event(tools.ics_to_unixepoch("20250101T173000Z"), tools.ics_to_unixepoch("20250101T183000Z"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

event = Event(tools.cal_to_unixepoch("2025-01-01T18:30:00+01:00"), tools.cal_to_unixepoch("2025-01-01T19:30:00+01:00"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

# import python.googleutils as googleutils
# googleutils.download_calendar("c_2ed13b6f70a955f61b14ee956ea2b25bc153f66b2fb81a565e29881d3fad0882@group.calendar.google.com")