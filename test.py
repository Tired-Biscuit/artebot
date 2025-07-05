import python.db as db
import python.tools as tools
from python.classes.musician import Musician
from python.classes.event import Event

from dotenv import load_dotenv

load_dotenv()

try:
    print("Database reset...", db.reset(allow_fail=True))
    print("Database init...", db.init())
except Exception as e:
    print(e)
    pass

print("Updating database for Google calendars...", "Done" if db.update_calendars() == None else "An error occured")
print("Updating database for school-issued timetables...", "Done" if (res := db.update_timetables()) == [] else res)


db.add_user("1234", "toto@titi.com",  "fise_1a_g1")
db.add_user("4321", "paul.musial@telecomnancy.net",  "fise_1a_g2")
musician = Musician(id="1234")

assert(musician.id == "1234")
assert(musician.mail == "toto@titi.com")
assert(musician.group == "fise_1a_g1")

# db.add_punctual_constraint("1234", "01-01-2025", "18:30", "19:30")
db.add_new_punctual_constraint("4321", tools.local_to_unixepoch("20250901100000"), tools.local_to_unixepoch("20250901113000"))
db.add_new_punctual_constraint("1234", tools.local_to_unixepoch("20250901100000"), tools.local_to_unixepoch("20250901113000"))
db.add_new_recurring_constraint("4321", 32400, 37800, 1)
musician = Musician(id="1234")

event = Event(tools.ics_to_unixepoch("20250901T80000Z"), tools.ics_to_unixepoch("20250901T93000Z"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

event = Event(tools.cal_to_unixepoch("2025-09-01T10:00:00+02:00"), tools.cal_to_unixepoch("2025-09-01T11:30:00+02:00"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

print(db.request_blocking_events(tools.local_to_unixepoch("20250901100000"), 3600, "4321"))
# print(db.request_blocking_google_events(local_to_unixepoch("20250901100000"), "4321"))
# import python.googleutils as googleutils
# googleutils.download_calendar("c_2ed13b6f70a955f61b14ee956ea2b25bc153f66b2fb81a565e29881d3fad0882@group.calendar.google.com")