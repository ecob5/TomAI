-- AI assistance disclosure (CS50): an AI assistant proposed this initial
-- schema. The student must review and adapt every table before submission.

DROP TABLE IF EXISTS dose_records;
DROP TABLE IF EXISTS schedules;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    instructions TEXT,
    stock_quantity INTEGER CHECK (stock_quantity IS NULL OR stock_quantity >= 0),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    reminder_time TEXT NOT NULL
        CHECK (
            length(reminder_time) = 5
            AND reminder_time GLOB '[0-2][0-9]:[0-5][0-9]'
            AND substr(reminder_time, 1, 2) BETWEEN '00' AND '23'
        ),
    days_of_week TEXT NOT NULL DEFAULT '0,1,2,3,4,5,6',
    start_date TEXT,
    end_date TEXT,
    FOREIGN KEY (medication_id) REFERENCES medications (id) ON DELETE CASCADE
);

CREATE TABLE dose_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schedule_id INTEGER NOT NULL,
    scheduled_for TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'taken', 'skipped', 'missed', 'snoozed')),
    responded_at TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules (id) ON DELETE CASCADE,
    UNIQUE (schedule_id, scheduled_for)
);

CREATE INDEX idx_medications_user ON medications (user_id);
CREATE INDEX idx_schedules_medication ON schedules (medication_id);
CREATE INDEX idx_dose_records_schedule ON dose_records (schedule_id);
