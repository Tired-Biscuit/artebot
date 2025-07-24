# ArtéBot

## Description

The aim of this project is to help members of the Bureau Des Arts, particularly the musicians, to plan rehearsals.

The bot should offer time slots for rehearsals while taking into account the scholar schedule of each member, their personal availability, the school's opening hours, and the rehearsals room's availability.

## Requirements

Python 3.11 minimum (venv recommended)

run the following to install any dependency in requirements.txt:

```sh
pip install -r requirements.txt
```

If you want to setup a virtual environment, do not forget to activate it before!



## Setup

The project needs a Google Apps Script in a project to run. You may need to create a Google Cloud Project (GCP) and associate the Apps Script to it.

To get the credentials.json, you need to create a OAuth 2.0 Client ID as 'Desktop Application', see the google quickstart guide for python integration for more info. Put it in the root of the repo.

In the root of the project, create a .env file (or remove the .example at the end of the commited file) with the following content:

```py
DISCORD_TOKEN=... # Token for the production-ready bot here
DEV_TOKEN=... # Token for the beta bot here
SCRIPT_ID=... # Id of the API Google Apps script containing the script (in script.js)
```