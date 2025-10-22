import python.db as db
import python.tools as tools
from python.classes.musician import Musician
from python.classes.event import Event
import python.googleutils as googleutils

from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

db.TESTING_DATABASE = True
db.refresh()

""" try:
    print("Database reset...", db.reset(allow_fail=True))
    print("Database init...", db.init())
except Exception as e:
    print(e)
    pass

# print("Updating database for Google calendars...", "Done" if (result := db.update_calendars()) == None else f"An error occured: {result}")
# print("Updating database for school-issued timetables...", "Done" if (res := db.update_timetables()) == [] else res)


db.add_user("1234", "toto le goat", "toto@titi.com",  "fise_1a_g1")
db.add_user("4321", "pol", "paul.musial@telecomnancy.net",  "fise_1a_g2")
musician = Musician(id="1234")

assert(musician.id == "1234")
assert(musician.mail == "toto@titi.com")
assert(musician.group == "fise_1a_g1")

# db.add_punctual_constraint("1234", "01-01-2025", "18:30", "19:30")
db.add_punctual_constraint("4321", tools.local_to_unixepoch("20250901100000"), tools.local_to_unixepoch("20250901113000"))
db.add_punctual_constraint("1234", tools.local_to_unixepoch("20250901100000"), tools.local_to_unixepoch("20250901113000"))
db.add_recurring_constraint("4321", 32400, 37800, 1)
musician = Musician(id="1234")

event = Event(tools.ics_to_unixepoch("20250901T80000Z"), tools.ics_to_unixepoch("20250901T93000Z"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

event = Event(tools.cal_to_unixepoch("2025-09-01T10:00:00+02:00"), tools.cal_to_unixepoch("2025-09-01T11:30:00+02:00"))
assert(musician.events[0].start_time == event.start_time)
assert(musician.events[0].end_time == event.end_time)

# print(db.request_blocking_events(tools.local_to_unixepoch("20250901100000"), 3600, "4321"))
# print(googleutils.get_spreadsheet_columns_names("1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM"))

data={
    "sheets": [
        {
            "data": [
                {
                    "rowData": [
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        "stringValue": "New York City Cops"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "The Strokes"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Rock"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Tom LOISIL"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "tom.loisil@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "numberValue": 0.002476851851851852
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Paul MUSIAL Tom LOISIL"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "paul.musial@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        },
                                        {
                                            "startIndex": 11
                                        },
                                        {
                                            "startIndex": 12,
                                            "chip": {
                                                "personProperties": {
                                                    "email": "tom.loisil@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        },
                                        {
                                            "startIndex": 22
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "? + ?"
                                    }
                                },
                                {},
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "9/11 reference??"
                                    }
                                }
                            ]
                        },
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Scar Tissue"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Red Hot Chili Peppers"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Rock"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Paul MUSIAL"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "paul.musial@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "numberValue": 0.0025
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Paul MUSIAL Tom LOISIL"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "paul.musial@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        },
                                        {
                                            "startIndex": 11
                                        },
                                        {
                                            "startIndex": 12,
                                            "chip": {
                                                "personProperties": {
                                                    "email": "tom.loisil@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        },
                                        {
                                            "startIndex": 22
                                        }
                                    ]
                                },
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Ga\u00ebl CONSTANT"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "gael.constant@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Us And Them"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Pink Floyd"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Pink Floyd \ud83d\udc40"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Paul MUSIAL"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "paul.musial@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "numberValue": 0.005439814814814815
                                    }
                                },
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "synth\u00e9 + piano"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Cl\u00e9ment PIGASSOU"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "clement.pigassou@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {},
                                {},
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                }
                            ]
                        },
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        "stringValue": "It Ain't Over 'Til It's Over"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Lenny Kravitz"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Rock"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Nathan LI\u00c9NARD"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "nathan.lienard@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "numberValue": 0.0026041666666666665
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Nathan LI\u00c9NARD"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "nathan.lienard@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Cl\u00e9ment PIGASSOU"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "clement.pigassou@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "values": [
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Slide Away"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Oasis"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Rock"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Nathan LI\u00c9NARD"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "nathan.lienard@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        }
                                    ]
                                },
                                {
                                    "userEnteredValue": {
                                        "numberValue": 0.0045138888888888885
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "Nathan LI\u00c9NARD + ?"
                                    },
                                    "chipRuns": [
                                        {
                                            "chip": {
                                                "personProperties": {
                                                    "email": "nathan.lienard@telecomnancy.net",
                                                    "displayFormat": "DEFAULT"
                                                }
                                            }
                                        },
                                        {
                                            "startIndex": 14
                                        }
                                    ]
                                },
                                {},
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                },
                                {
                                    "userEnteredValue": {
                                        "stringValue": "?"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

# print(googleutils.get_spreadsheet_name("1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM"))



import time
# from datetime import datetime
# print(datetime.strptime("1000", "%H%M").replace(tzinfo=tools.timezone.utc).replace(year=1970).timestamp())

# googleutils.print_data_info(data)
# db.add_setlist("1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM", 50)
# print(googleutils.get_spreadsheet_name(googleutils.get_spreadsheet_id("https://docs.google.com/spreadsheets/d/1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM/edit?usp=sharing")))
# print(googleutils.execute_api_function("extractSmartChipEmails", ["1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM", googleutils.get_sheet_name("1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM"), "D"]))

# print(googleutils.execute_api_function("check"))
# googleutils.download_spreadsheet("1Znt6wvGPQalQ_sqBNBbKTGlACgu2MKDxOIwcJRTpDVM")
# print(db.request_blocking_google_events(local_to_unixepoch("20250901100000"), "4321"))
# import python.googleutils as googleutils
# googleutils.download_calendar("c_2ed13b6f70a955f61b14ee956ea2b25bc153f66b2fb81a565e29881d3fad0882@group.calendar.google.com")

 """

tomorrow = datetime.now() + timedelta(days=1)
start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
end_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)

event = {
    "summary": "Test Event",
    "description": "This is a test event added via API.",
    "start": {
        "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": "Europe/Paris"
    },
    "end": {
        "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        "timeZone": "Europe/Paris"
    }
}
calendar_id = "c_67370f068ccc5eaaafb4d663645dca79e62e8675a5a4619c2510134fb5ec746e@group.calendar.google.com"
success = googleutils.add_event_to_calendar(calendar_id, event)
print("Test event added:", success)