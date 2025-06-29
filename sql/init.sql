CREATE TABLE Song(
    title TEXT,
    artist TEXT,
    length TIME,
    supervisor TEXT,
    voice TEXT,
    guitar TEXT,
    keys TEXT,
    drums TEXT,
    bass TEXT,
    violin TEXT,
    cello TEXT,
    contrabass TEXT,
    accordion TEXT,
    flute TEXT,
    saxophone TEXT,
    horn TEXT,
    notes TEXT
);

CREATE TABLE User(
    uuid INTEGER UNIQUE,
    email TEXT,
    group_id INTEGER
);

CREATE TABLE SchoolEvent(
    uuid INTEGER,
    group_id TEXT,
    start_time DATETIME,
    end_time DATETIME,
    duration INT,
    subject TEXT,

    CONSTRAINT pk_school_event UNIQUE (uuid, group_id)
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