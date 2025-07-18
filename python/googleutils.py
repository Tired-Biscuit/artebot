from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import errors
from googleapiclient.discovery import build
import python.tools as tools
import requests
import json

import os

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.scriptapp',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets'
]

def refresh_token():
    """
    Creates or refresh token if necessary
    
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

def execute_api_function(function_name: str, opt_param=None):
    """
    Executes the corresponding API function with optionnal parameters between brackets if needed.

    Returns: (bool, str), if bool is true, execution was a success and str is the result
            else, srt is the error message. 
    """
    creds = refresh_token()
    try:
        service = build("script", "v1", credentials=creds)
        
        script_id = os.getenv("SCRIPT_ID")

        print(script_id)

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

def download_calendar(calendar_id):
    """
    Fetch the calendar

    Returns: (bool, str/list) if bool is True, it's a success and the second item is a list of event,
                else, it's a string of the error message
    """
    creds = refresh_token()

    url = f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events"
    print(url)

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    params = {
        # "timeMin": "2025-06-01T00:00:00Z",
        # "timeMax": "2025-06-30T23:59:59Z",
        "singleEvents": True,
        "orderBy": "startTime"
    }

    response = requests.get(url, headers=headers)#, params=params)

    if response.status_code == 200:
        data = response.json()
        
        with open("temp_cal2.json", "w") as f:
            
            f.write(json.dumps(data))
        return (True, data["items"])
        # for event in data.get("items", []):
        #     print(event["summary"], event.get("start"), event.get("end"))
    else:
        print("Erreur :", response.status_code, response.text)
        return (False, response.text)

def get_spreadsheet_id(spreadsheet_link: str) -> str:
    return spreadsheet_link.split("/")[5]

def get_sheet_name(spreadsheet_id: str) -> str:
    creds = refresh_token()

    # Get the first sheet's name
    meta_url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?fields=sheets.properties'
    meta_headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }
    meta_response = requests.get(meta_url, headers=meta_headers)
    if meta_response.status_code != 200:
        print("Erreur:", meta_response.status_code, meta_response.text)
        return meta_response.text
    meta_data = meta_response.json()
    first_sheet_title = meta_data["sheets"][0]["properties"]["title"]
    return first_sheet_title

def get_setlists_names() -> list[str] | None:
    names = []
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            setlists_ids = json.loads(f.read())["setlists"]
            for setlist_id in setlists_ids:
                names.append(get_sheet_name(setlist_id))
            return names
    return None

def download_spreadsheet(spreadsheet_id) -> str:
    """
    Fetches the first sheet of the spreadsheet

    Returns: the error text in case of error
    """

    first_sheet_title = get_sheet_name(spreadsheet_id)

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&headers=0&sheet={first_sheet_title}"

    creds = refresh_token()

    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)#, params=params)

    if response.status_code == 200:
        data = response.text
        print("miaou")
        with open("setlist.csv", "w") as f:
            f.write(data)

    else:
        print("Erreur :", response.status_code, response.text)
        return response.text

def get_spreadsheet_data(spreadsheet_id):
    """
    Executes a request to Google Sheets API and returns the response
    """

    creds = refresh_token()

    service = build('sheets', 'v4', credentials=creds)

    request = service.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        includeGridData=True,
        ranges=[f"{get_sheet_name(spreadsheet_id)}!{'A2:R6'}"],
        fields="sheets(data(rowData(values(userEnteredValue,chipRuns))))"
        # fields="sheets(data(rowData(values(effectiveValue,userEnteredValue,formattedValue,hyperlink))))"
    )

    response = request.execute()

    return response

def print_data_info(data: dict):
    data = data["sheets"][0]["data"][0]
    rows = data["rowData"]
    for row in rows:
        print(json.dumps(get_song_info_from_row_values(row["values"]), sort_keys=False, indent=4))

def get_chip_emails_from_cell_values(cell_values: dict) -> list[str]:
    """
    Parses the fetched content of the cell given in parameter to return a list of all emails
    """
    emails = []
    if "chipRuns" not in cell_values.keys():
        return emails
    for chip in cell_values["chipRuns"]:
        if "chip" in chip.keys():
         emails.append(chip["chip"]["personProperties"]["email"])
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
            result = int(float(cell_values["userEnteredValue"]["numberValue"])*tools.DAY_DURATION)

    return result

def get_emails_strings(emails: list[str]) -> str:
    result = ""
    for email in emails:
        result += email + " "
    return result[:-1]

def get_song_info_from_row_values(row_values: dict) -> dict:
    """
    Parses the row values fetched from sheets and returns a dictionary compliant with the db
    """
    song = {"title":"",
    "artist":"",
    "length":"",
    "supervisor":"",
    "voice":"",
    "guitar":"",
    "keys":"",
    "drums":"",
    "bass":"",
    "violin":"",
    "cello":"",
    "contrabass":"",
    "accordion":"",
    "flute":"",
    "saxophone":"",
    "brass":"",
    "notes":""}

    song["title"] = get_text_cell_content(row_values[0])
    song["artist"] = get_text_cell_content(row_values[1])
    song["supervisor"] = get_email_from_cell_values(row_values[3])
    song["length"] = get_time_cell_content(row_values[4])

    keys = list(song.keys())

    for k in range(5,len(row_values)):
        if k-1 >= len(keys):
            print("Error:", song["title"], str(row_values))
            return song
        song[keys[k-1]] = get_emails_strings(get_chip_emails_from_cell_values(row_values[k]))
        if keys[k-1] == "notes":
            song[keys[k-1]] = get_text_cell_content(row_values[k])
    return song

