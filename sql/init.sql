CREATE TABLE Song(
    setlist_id TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL DEFAULT '',
    artist TEXT NOT NULL DEFAULT '',
    length TIME NOT NULL DEFAULT 0,
    notes TEXT NOT NULL DEFAULT '',
    supervisor TEXT NOT NULL DEFAULT '',
    voice TEXT NOT NULL DEFAULT '',
    guitar TEXT NOT NULL DEFAULT '',
    keys TEXT NOT NULL DEFAULT '',
    drums TEXT NOT NULL DEFAULT '',
    bass TEXT NOT NULL DEFAULT '',
    violin TEXT NOT NULL DEFAULT '',
    cello TEXT NOT NULL DEFAULT '',
    contrabass TEXT NOT NULL DEFAULT '',
    accordion TEXT NOT NULL DEFAULT '',
    flute TEXT NOT NULL DEFAULT '',
    saxophone TEXT NOT NULL DEFAULT '',
    brass TEXT NOT NULL DEFAULT ''
);

CREATE TABLE User(
    uuid INTEGER UNIQUE,
    username TEXT,
    email TEXT UNIQUE,
    group_id INTEGER
);

CREATE TABLE SchoolEvent(
    uuid INTEGER,
    group_id TEXT,
    start_time DATETIME,
    end_time DATETIME,
    duration INT,
    name TEXT,

    CONSTRAINT pk_school_event UNIQUE (uuid, group_id, start_time, end_time)
);

CREATE TABLE GoogleEvent(
    uuid TEXT,
    calendar_id TEXT,
    musicians TEXT,
    start_time DATETIME,
    end_time DATETIME,
    name TEXT,

    CONSTRAINT pk_google_event UNIQUE (uuid, calendar_id)
);

CREATE TABLE MusicianConstraint(
    musician_uuid TEXT,
    day DATE,
    start_time TIME,
    end_time TIME,
    week_day INTEGER,

    CONSTRAINT pk_musician_constraint UNIQUE (musician_uuid, day, start_time, end_time, week_day),
    FOREIGN KEY (musician_uuid) REFERENCES User(uuid)
)