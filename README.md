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

Three files are needed for this project to run. When starting the docker container, make sure to have them in the same directory you run the command.

The project needs a Google Apps Script in a project to run. You may need to create a Google Cloud Project (GCP) and associate the Apps Script to it.

To get the credentials.json, you need to create a OAuth 2.0 Client ID as 'Desktop Application', see the Google quickstart guide for python integration for more info. Put it in the root of the repo.
Before running the project, you need to authorize the credentials and create your first token.json file. You can get it by running token_init.py and opening the printed out link. Should you change your working directory, make sure to bring theses two files with you.


In the root of the project, create a .env file (or remove the .example at the end of the commited file) with the following content:

You can change the .env file (to change tokens or debug state) before starting the container, and they will be applied.

```py
DEV_TOKEN=Mlkjh...l35467j # Token for the production bot here
DISCORD_TOKEN=LMLhk9876MzM...9aljk5yE # Token for the testing bot here
SCRIPT_ID=AKfycbzkhfj....dsflkjj # Id of the API Google Apps script containing the script (in script.js)
DEBUG= # Leave empty for production bot or put 1 for debug bot
```

## Starting the app

# Using Docker compose
In a directory containing at least your .env, token.json, credentials.json, and the docker-compose.yml:
```shell
$ docker compose up -d
```
Shut it down with the following command (still in the directory):
```shell
$ docker compose down
```

# Manually creating containers from image:
Note that you might need to create the necessary volumes by yourself.

# Browsing Volumes

Two volumes are needed (created and mounted automatically with docker compose): data_volume and db_volume.
To browse their content, it is recommended to first shut the container, and then execute the following:
```shell
docker run --rm -it -v artebot_data_volume:/mnt alpine sh
```
or artebot_db_volume. Note that sqlite3 is not installed in the alpine image.

# Replacing volume files

To copy a file in your current directory inside the volume (example with import of a data.json file):
```shell
docker run --rm -v artebot_data_volume:/mnt -v $(pwd):/host alpine sh -c "cp /host/data.json /mnt/"
```

# Exporting volumes

```shell
docker run --rm -v artebot_data_volume:/volume -v $(pwd):/backup busybox tar czf /backup/data_backup.tar.gz -C /volume .
```