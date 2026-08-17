"""SQLite connection and initialization helpers for TomAI.

AI assistance disclosure (CS50): an AI assistant helped scaffold this module.
The student must review and understand the database lifecycle used here.
"""

import sqlite3

import click
from flask import current_app, g


def get_db():
    """Open one database connection per request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db


def close_db(_error=None):
    """Close the current request's database connection, if one exists."""
    database = g.pop("db", None)

    if database is not None:
        database.close()


def init_db():
    """Create the database tables from schema.sql."""
    database = get_db()

    with current_app.open_resource("schema.sql") as schema_file:
        database.executescript(schema_file.read().decode("utf-8"))


@click.command("init-db")
def init_db_command():
    """Reset the local database from the command line."""
    init_db()
    click.echo("Initialized the TomAI database.")


def init_app(app):
    """Register database helpers with the Flask application."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
