# ArtéBot

## Description

The aim of this project is to help members of the Bureau Des Arts, particularly the musicians, to plan rehearsals.

The bot should offer time slots for rehearsals while taking into account the scholar schedule of each member, their personal availability, the school's opening hours, and the rehearsals room's availability.

## Requirements

Python 3.11 minimum (venv recommended)

run the following to install any dependency in requirements.txt:

```
pip install -r requirements.txt
```

If you want to setup a virtual environment, do not forget to activate it before!



## Setup (automation for Linux only)

In the root of the project, create a .env file (or remove the .example at the end of the commited file) with the following content:

```
DISCORD_TOKEN=JHK....JDFML5432ndf # Token for the production-ready bot here
DEV_TOKEN=SDLKJf.....21df3dsf # Token for the beta bot here
```

For automatic timetables fetching, schedule the task with cron

```
crontab -e
```

And add the following line at the end (note: replace with absolute path to repo, e.g. use pwd):

```
* 6 * * * cd /path/to/repo/ && ./cron/auto_update.sh
```