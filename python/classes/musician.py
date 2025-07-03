from python.classes.event import *
import python.db as db

class Musician:
    """
    Represents a musician with a list of events.
    """

    def __init__(self, mail: str):

        id = db.run(f"SELECT uuid FROM User WHERE email = '{mail}'")

        if not id:
            raise ValueError(f"User with email {mail} does not exist.")
        
        self.id = id[0][0]

        events = db.run(f"SELECT * FROM MusicianConstraint WHERE musician = '{self.id}' AND week_day = 0;")

        recurring_events = db.run(f"SELECT * FROM MusicianConstraint WHERE musician = '{self.id}' AND week_day != 0;")

        self.events = constraints_to_events(events)
        self.recurring_events = recurring_constraints_to_events(recurring_events)

        self.group = db.run(f"SELECT group_id FROM User WHERE email = '{mail}'")[0][0]