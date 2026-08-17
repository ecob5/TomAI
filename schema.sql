DROP TABLE IF EXISTS dose_records;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    instructions TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    reminder_time TEXT NOT NULL CHECK (
        length(reminder_time) = 5
        AND reminder_time GLOB '[0-2][0-9]:[0-5][0-9]'
        AND substr(reminder_time, 1, 2) BETWEEN '00' AND '23'
    ),
    FOREIGN KEY (medication_id) REFERENCES medications (id) ON DELETE CASCADE
);

CREATE TABLE dose_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    scheduled_for TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('taken', 'skipped')),
    responded_at TEXT,
    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE,
    UNIQUE (schedule_id, scheduled_for)
);

CREATE INDEX medications_by_user ON medications (user_id);
CREATE INDEX schedules_by_medication ON schedules (medication_id);
