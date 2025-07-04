from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient import errors
from googleapiclient.discovery import build

import requests
import json

import os

# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.scriptapp',
    'https://www.googleapis.com/auth/calendar'
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
    Executes the corresponding API function with the optionnal parameter if needed.

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
            request["parameters"] = [opt_param]

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
        print("Erreur:", response.status_code, response.text)
        return (False, response.text)
