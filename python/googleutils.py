from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import errors
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import python.tools as tools
import python.timeutils as timeutils
import requests
import json
import python.db as db

import os


class NoCalendarError(Exception):
    def __init__(self):
        super().__init__("No calendar is linked")

class ExistingCalendarError(Exception):
    def __init__(self, calendar_id):
        super().__init__(f"Cette setlist a déjà un calendrier ! https://calendar.google.com/calendar/u/0/r?cid={calendar_id}")

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.scriptapp',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

def refresh_token():
    """
    Creates or refreshes token if necessary
    
    Returns the credentials or None if creds couldn't be acquired
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    return creds

def execute_api_function(function_name: str, opt_param=None) -> tuple[bool, str]:
    """
    Executes the corresponding API function with optionnal parameters between brackets if needed.

    Returns: (bool, str), if bool is true, execution was a success and str is the result
            else, srt is the error message. 
    """
    creds = refresh_token()
    try:
        service = build("script", "v1", credentials=creds)
        
        script_id = os.getenv("SCRIPT_ID")

        print("Script id:", script_id)

        request = {
            "function": function_name,
            "devMode": True
        }
        if (opt_param):
            request["parameters"] = opt_param

        response = service.scripts().run(scriptId=script_id, body=request).execute()
        try:
            result = response["response"]["result"]
            return (True, result)
        except:
            return (False, response)

    except errors.HttpError as error:
        # The API encountered a problem.
        return (False, error.content)


def test_calendar(calendar_id: str) -> bool | None:
    """
    Tries to reach calendar and returns if it is a success or raises an error
    """
    creds = refresh_token()
    service = build("calendar", "v3", credentials=creds)

    result = service.calendars().get(calendarId=calendar_id, fields="summary")

    return result


def download_calendar(calendar_id: str) -> tuple[bool, str|list]:
    """
    Fetch the Google Calendar events

    Returns: (bool, str/list) if bool is True, it's a success and the second item is a list of event,
                else, it's a string of the error message
    """
    creds = refresh_token()
    service = build("calendar", "v3", credentials=creds)

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            singleEvents=True,
            orderBy="startTime",
            # timeMin="2025-06-01T00:00:00Z",
            # timeMax="2025-06-30T23:59:59Z",
        ).execute()
        events = events_result.get("items", [])
        #TODO delete in production
        # with open("temp_cal.json", "w") as f:
        #     f.write(json.dumps(data))

        return (True, events)

    except HttpError as error:
        response = f"Erreur {error.status_code}: {error}"
        return (False, response)


def add_event_to_calendar(calendar_id:str, event:dict) -> str:
    """
    Add an event into a Google calendar

    Returns event id
    """
    creds = refresh_token()
    service = build('calendar', 'v3', credentials=creds)
    try:
        response = service.events().insert(calendarId=calendar_id, body=event).execute()
        result = download_calendar(calendar_id)
        if result[0]:
            db.update_calendar(result[1])
    except HttpError as error:
        raise error
    return response["id"]


def remove_event_from_calendar(calendar_id: str, event_id: str) -> bool:
    """
    Remove an event from a Google calendar

    Returns success state
    """
    creds = refresh_token()
    service = build('calendar', 'v3', credentials=creds)
    try:
        response = service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        result = download_calendar(calendar_id)
        if result[0]:
            db.update_calendar(result[1])
    except HttpError as error:
        raise error
    return response


def add_rehearsal_to_calendar(song:str, attendees:list[str], creator:str, start_time:str, end_time:str) -> bool:
    """
    Adds rehearsal to Google Calendar and returns if operation was successful
    """

    song_info = db.get_song_info(song)

    instruments_names = db.get_instruments_names()

    musicians_instruments = dict()

    for i in range(4, len(song_info)-1):
        if song_info[i]:
            musicians = song_info[i].split(" ")
            for musician in musicians:
                if musician not in musicians_instruments:
                    musicians_instruments[musician] = instruments_names[i][0].capitalize()
                else:
                    musicians_instruments[musician] += ", " + instruments_names[i][0]

    event = {
        "summary": f"Répétition {song_info[1]}",
        "description": f"Répétition pour {song_info[1]} ({song_info[2]})",
        "start": {
            "dateTime": start_time,
            "timeZone": "Europe/Paris"
        },
        "end": {
            "dateTime": end_time,
            "timeZone": "Europe/Paris"
        },
        "attendees": [{"email": k, "comment": v} for k, v in musicians_instruments.items() if k in attendees or not attendees],
        "location": "Local",
        "creator": {"displayName": creator},
        "organizer": {"email": song_info[4]},
        "guestsCanModify": True
    }
    calendar_id = tools.get_setlist_calendar_id(song_info[0])
    if calendar_id:
        try:
            result = add_event_to_calendar(calendar_id, event)
        except Exception as e:
            print("The following request was not successful:", event)
            raise e
        calendar = download_calendar(calendar_id)[1]
        db.update_calendar(calendar)
        if result:
            return True
    else:
        raise NoCalendarError


def get_calendar_id(calendar_link: str):
    if calendar_link is not None:
        if len(calendar_link.split("=")) > 1:
            return calendar_link.split("=")[1]

def create_calendar(name: str, sheet_id: str) -> str | None:
    """
    Creates a calendar for a given sheet

    Returns the id of the newly created calendar
    """
    creds = refresh_token()
    service = build('calendar', 'v3', credentials=creds)
    body = {
        "summary": name,
        "description": f"Calendrier pour les répétitions de l’évènement « {name} ». Setlist : https://docs.google.com/spreadsheets/d/{sheet_id}",
        "timeZone": "Europe/Paris"

    }

    try:
        response = service.calendars().insert(body=body).execute()
        response = response["id"]
    except HttpError as error:
        response = f"Erreur {error.status_code}: {error}"
    return response


def share_calendar(calendar_id):
    creds = refresh_token()
    service = build('calendar', 'v3', credentials=creds)
    rule = {
    'scope': {
        'type': 'domain',
        'value': 'esial.net'
        },
        'role': 'writer'
    }

    created_rule = service.acl().insert(calendarId=calendar_id, body=rule).execute()
    return created_rule


def get_calendar_share_link(setlist_id: str) -> str:
    """
    Returns the calendar link for a setlist

    @flag data
    @flag setlist
    @flag calendar
    """
    calendar_id = tools.get_setlist_calendar_id(setlist_id)
    return f"https://calendar.google.com/calendar/u/0/r?cid={calendar_id}"


def delete_calendar(calendar_id: str) -> str:
    """
    Deletes a calendar
    """
    creds = refresh_token()
    service = build('calendar', 'v3', credentials=creds)

    try:
        response = service.calendars().delete(calendarId=calendar_id).execute()
    except HttpError as error:
        response = f"Erreur {error.status_code}: {error}"
    return response


def create_setlist_calendar(setlist_id: str) -> str:
    """
    Creates a calendar for a given setlist and updates data.json

    Returns the id of the newly created calendar
    """
    calendar = tools.get_setlist_calendar_id(setlist_id)
    if calendar:
        raise ExistingCalendarError(calendar)

    result = create_calendar(tools.get_setlist_name(setlist_id), setlist_id)

    if not result:
        raise Exception("Problème lors de la création du calendrier")

    share_calendar(result)
    tools.add_calendar(result)
    tools.add_calendar_to_setlist(setlist_id, result)

    return f"https://calendar.google.com/calendar/u/0/r?cid={result}"


def get_spreadsheet_id(spreadsheet_link: str) -> str:
    return spreadsheet_link.split("/")[5]

def get_sheet_name(spreadsheet_id: str) -> str:
    """
    Get the first sheet's name
    """
    creds = refresh_token()

    service = build('sheets', 'v4', credentials=creds)

    request = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets.properties.title"
    )

    try:
        response = request.execute()["sheets"][0]["properties"]["title"]
    except HttpError as error:
        response = f"Erreur {error.status_code}: {error}"

    return response


def get_spreadsheet_name(spreadsheet_id: str) -> str:
    creds = refresh_token()

    service = build('sheets', 'v4', credentials=creds)

    request = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="properties.title"
    )

    response = request.execute()["properties"]["title"]
    return response

def get_setlists_names() -> list[str] | None:
    """
    Gets a list of the names of the setlists in the data.json file.

    @flag data
    """
    names = []
    if os.path.exists(tools.datafile_path):
        with open(tools.datafile_path, "r") as f:
            setlists_ids = json.loads(f.read())["setlists"]
            for setlist_id in setlists_ids:
                names.append(setlist_id[1])
            return names
    return None

def get_spreadsheet_data(spreadsheet_id: str, rows: int) -> dict:
    """
    Executes a request to Google Sheets API and returns the response
    """

    creds = refresh_token()

    service = build('sheets', 'v4', credentials=creds)

    request = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=True,
        ranges=[f"{get_sheet_name(spreadsheet_id)}!{f'A1:R{rows+1}'}"],
        fields="sheets(data(rowData(values(userEnteredValue,chipRuns))))"
        # fields="sheets(data(rowData(values(effectiveValue,userEnteredValue,formattedValue,hyperlink))))"
    )

    response = request.execute()

    return response

def print_data_info(data: dict, setlist_id: str):
    data = data["sheets"][0]["data"][0]
    rows = data["rowData"]
    for row in rows:
        print(json.dumps(get_song_info_from_row_values(row["values"], setlist_id), sort_keys=False, indent=4))

def get_chip_emails_from_cell_values(cell_values: dict) -> list[str]:
    """
    Parses the fetched content of the cell given in parameter to return a list of all emails
    """
    emails = []
    if "chipRuns" not in cell_values.keys():
        return emails
    for chip in cell_values["chipRuns"]:
        if "chip" in chip.keys():
            try:
                emails.append(chip["chip"]["personProperties"]["email"])
            except:
                raise Exception(f"Erreur pour le chip suivant: {chip}")
    return emails

def get_email_from_cell_values(cell_values: dict) -> str:
    """
    Fetches only the first email in a People Chip cell
    """
    result = ""
    if "chipRuns" in cell_values.keys() and len(cell_values["chipRuns"]) > 0:
        if "chip" in cell_values["chipRuns"][0].keys():
            result = cell_values["chipRuns"][0]["chip"]["personProperties"]["email"]
    return result

def get_text_cell_content(cell_values: dict) -> str:
    """
    Returns the displayed cell content in a string
    """
    result = ""
    if "userEnteredValue" in cell_values.keys():
        if "stringValue" in cell_values["userEnteredValue"].keys():
            result = cell_values["userEnteredValue"]["stringValue"]

    return result

def get_time_cell_content(cell_values: dict) -> int:
    """
    Returns the time in EPOCH
    """
    result = ""
    if "userEnteredValue" in cell_values.keys():
        if "numberValue" in cell_values["userEnteredValue"].keys():
            result = int(float(cell_values["userEnteredValue"]["numberValue"])*timeutils.DAY_DURATION)

    return result

def get_emails_strings(emails: list[str]) -> str:
    result = ""
    for email in emails:
        result += email + " "
    return result[:-1]

def get_song_info_from_row_values(row_values: dict, setlist_id: str, column_names: list[str], db_columns: list[str]) -> dict:
    """
    Parses the row values fetched from sheets and returns a dictionary compliant with the db
    """
    song = {}

    translation_dict = tools.get_instruments_names_translation()

    translated_columns = []
    for translations in translation_dict.values():
        for value in translations:
            translated_columns.append(value)

    for i in range(min(len(column_names), len(row_values))):

        if column_names[i] not in translated_columns and column_names[i] not in tools.get_ignored_column_names():
            pass
        #     print("Attention, un instrument n’est pas enregistré dans la base de données :", column_names[i])
        else:
            for db_column in db_columns:
                if column_names[i] in translation_dict[db_column]:
                    if db_column in ["title", "artist", "notes"]:
                        value = get_text_cell_content(row_values[i])
                    elif db_column == "length":
                        value = get_time_cell_content(row_values[i])
                    elif db_column == "supervisor":
                        value = get_email_from_cell_values(row_values[i])
                    else:
                        value = get_emails_strings(get_chip_emails_from_cell_values(row_values[i]))
                    song[db_column] = value

    song["setlist_id"] = setlist_id

    # print("Song:", song)

    return song

def get_row_text(row: dict) -> list[str]:
    row_content = []
    for value in row["values"]:
        row_content.append(get_text_cell_content(value))
    return row_content