from python.classes.event import *
import python.db as db

class Musician:
    """
    Represents a musician with a list of its constraints as Event.

    Instanciate from either email address or uuid
    """

    def __init__(self, *, mail: str = "", id: str = ""):
        self.id: str
        self.mail: str
        self.events: list[Event]
        self.recurring_events: list[RecurringEvent]
        self.group: str

        if (mail != "" and id == ""):
            id = db.run("SELECT uuid FROM User WHERE email = ?;", (mail,))

            if not id:
                raise ValueError(f"User with email {mail} does not exist.")

            self.mail = mail
            self.id = id[0][0]

        elif (mail == "" and id != ""):
            mail = db.run("SELECT email FROM User WHERE uuid = ?;", (id,))

            if not mail:
                raise ValueError(f"User with uuid {id} does not exist.")

            self.mail = mail[0][0]
            self.id = id

        else:
            raise ValueError("Either multiple or no parameters were given, or they were null")

        events = db.run("SELECT * FROM MusicianConstraint WHERE musician_uuid = ? AND week_day = 0;", (self.id,))

        recurring_events = db.run("SELECT * FROM MusicianConstraint WHERE musician_uuid = ? AND week_day != 0;", (self.id,))

        self.events = constraints_to_events(events)
        self.recurring_events = recurring_constraints_to_events(recurring_events)

        group = db.run("SELECT group_id FROM User WHERE email = ?;", (self.mail,))
        if not group:
            raise Exception(f"Could not find group id for user with email '{self.mail}' and uuid '{self.id}'")
        self.group = group[0][0]