# TomAI

#### Video Demo: TODO

#### Description

TomAI is a medication scheduling and adherence tracking web application being
developed as a final project for CS50x. Its goal is to help users organize the
medication instructions they have already received and remember when each dose
is due. TomAI is not intended to diagnose, prescribe, recommend dosages, or
replace professional medical advice.

The application includes a small working flow: users can create an account,
sign in, add a medication with a daily time, see today's doses, mark a dose as
taken or skipped, and remove a medication. It intentionally stays simple and
does not send notifications or provide medical advice.

## Current files

- `app.py` creates the Flask application and defines the demo dashboard and
  about page routes.
- `templates/` contains the shared layout, dashboard, and about page.
- `static/styles.css` contains the responsive visual design.
- `requirements.txt` lists the Python dependency required by the application.

## Running locally

Create and activate a Python virtual environment, then install the dependency:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start Flask:

```powershell
flask --app app run --debug
```

Open `http://127.0.0.1:5000` in a browser.

## Running the tests

The automated tests use a temporary database and do not modify local user data:

```powershell
python -m unittest discover -s tests -v
```

## Current limitations

The current version is an interface-only demonstration with sample data. It
does not include accounts, persistence, notifications, editing, inventory
tracking, or medical recommendations.

## AI assistance disclosure

An AI assistant helped brainstorm the project and scaffold its initial Flask
structure, database draft, starter templates, CSS, comments, and documentation.
The author is responsible for reviewing, understanding, adapting, and testing
all suggestions. Future AI assistance will be cited where used, in accordance
with the CS50 academic honesty policy.
