# TomAI

#### Video Demo: TODO

#### Description

TomAI is a medication scheduling and adherence tracking web application built
as my final project for CS50x. I chose this subject because medication routines
can become difficult to follow when a person has more than one item scheduled
during the day. A written list shows what should be taken, but it does not make
it easy to see what has already happened today. TomAI puts both pieces of
information on one dashboard: the saved routine and the status of today's
doses.

The application allows a user to create an account, log in, and save a
medication with its dosage, reminder time, and optional instructions. Saved
medications remain available after the page is reloaded or the application is
restarted because they are stored in SQLite rather than kept in a Python list.
Each reminder appears in the daily dose list. A dose begins as pending and can
then be marked as taken or skipped. The user can also remove a medication that
is no longer part of the routine.

TomAI is an organization tool, not a source of medical advice. It does not
diagnose conditions, choose medicines, recommend dosages, or determine whether
a skipped dose should be taken later. Users should enter only instructions they
have already received from a qualified health professional.

## How the application works

The home page has two different states. A visitor who is not logged in sees a
short introduction and links to create an account or log in. After
authentication, the same route becomes the user's dashboard. The dashboard
loads that user's medications and schedules from the database. It also joins
the schedule with any dose record created for the current date. If there is no
record yet, the interface displays the dose as pending.

Registration stores a password hash instead of the original password. After a
successful registration or login, the user's database ID is saved in the Flask
session. Routes that change medication data check this session before doing
anything. Their database queries also include the user ID, which prevents one
account from deleting or updating another account's records by changing an ID
in the URL.

Adding a medication creates two related rows: one in `medications` for the
medicine itself and another in `schedules` for its daily reminder time. When a
dose is marked, TomAI inserts a row in `dose_records`. The combination of the
schedule and scheduled date is unique, so clicking a different status later
updates the existing daily record instead of creating duplicates. Removing a
medication also removes its schedule and dose history through SQLite foreign
keys with cascading deletes.

## Project files

- `app.py` creates the Flask application and contains its routes. It handles
  registration, login, logout, dashboard queries, medication creation and
  removal, and daily dose updates. Form values are checked on the server before
  they are stored.
- `database.py` manages one SQLite connection per Flask application context. It
  closes that connection after each request and provides the `init-db` command
  used to build a fresh local database.
- `schema.sql` defines the four tables and their relationships. It also contains
  checks for reminder-time and dose-status values, uniqueness constraints, and
  indexes for the most common lookups.
- `templates/base.html` contains the shared page structure, navigation, flash
  messages, stylesheet link, and footer. The other templates extend this file
  so those elements do not have to be repeated.
- `templates/index.html` contains both the public introduction and the logged-in
  dashboard. Its forms post to Flask routes, while its loops render the database
  results passed in by `app.py`.
- `templates/auth.html` is shared by the registration and login pages. The
  `mode` value controls which heading, fields, and links are displayed.
- `templates/about.html` explains why the project exists and clearly states its
  medical limitations.
- `static/styles.css` contains the colors, typography, cards, form controls,
  dose-status labels, and responsive layout used throughout the site.
- `tests/test_app.py` creates a temporary database for every test. It checks the
  public pages, registration, duplicate-email handling, persistence, dose
  updates, deletion, cascading database behavior, and protection of private
  routes. The tests never modify the normal database in `instance/`.
- `requirements.txt` records the Flask version needed to run the project.

## Design choices

I kept one daily reminder time per medication instead of starting with a more
complicated calendar. This made the main workflow clear and left the database
open to future improvement: more schedule rows could later be attached to one
medication. I separated medications, schedules, and dose records rather than
putting everything in one table because they represent different things. A
medication is long-lived, a schedule describes when it is due, and a dose
record describes what happened on one date.

SQLite was a practical choice for this version because the complete database is
a local file and Flask can use it without a separate server. Parameterized SQL
queries are used throughout the application so form input is never joined
directly into a query string. I used server-rendered Jinja templates rather
than JavaScript for the main actions. This keeps the data flow visible: submit
a form, validate it in Flask, update the database, and redirect back to the
dashboard.

## Running locally

Create and activate a Python virtual environment, then install the dependency:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Initialize the database and start Flask:

```powershell
flask --app app init-db
flask --app app run --debug
```

Open `http://127.0.0.1:5000` in a browser. Running `init-db` again deletes the
existing local records and creates empty tables, so it should only be used when
a reset is intended. For a deployed version, the `SECRET_KEY` environment
variable should be set to a private, unpredictable value.

## Running the tests

Run the complete test suite from the project folder:

```powershell
python -m unittest discover -s tests -v
```

## Current limitations and possible improvements

The current version supports one daily time for each medication. It does not
send browser, email, or phone notifications, and it does not edit an existing
entry. A user can remove an incorrect entry and add it again. Possible future
work includes multiple reminder times, selected days of the week, an editing
screen, stock tracking, and a longer adherence history. Any future feature
would continue to avoid medical recommendations and focus only on information
entered by the user.

## AI assistance disclosure

An AI assistant helped brainstorm the project, review the Flask and SQLite
structure, reorganize parts of the code, expand the tests, and review this
documentation. I am responsible for understanding, adapting, and testing the
result, in accordance with the CS50 academic honesty policy.
