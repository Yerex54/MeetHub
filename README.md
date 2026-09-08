# MeetHub – Student Events and Meetups Platform

A Flask web application for discovering, creating, and joining campus events.
Built for the TAW (Technologies for Web Applications) final project using
Python, Flask, Peewee ORM, SQLite, HTML, CSS and Jinja2.

## Requirements

- Python 3.10+
- pip

## Setup

1. (Optional) Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python app.py
   ```

4. Open your browser at: http://127.0.0.1:5000

The included `database.db` already contains sample categories, events, and
a demo admin account, created automatically by `seed_data()` on first run.
Deleting `database.db` and re-running `app.py` will rebuild it from scratch
with the same sample data.

## Demo Credentials

**Admin account** (access to the backoffice at `/admin/events`):
- Username: `admin`
- Password: `admin123`

You can also register a new regular user account from the homepage to test
event registration as a normal user.

## Project Structure

| Item               | Purpose                                                          |
|---------------------|-------------------------------------------------------------------|
| `app.py`            | Flask routes: public pages, authentication, user area, backoffice |
| `models.py`          | Peewee ORM models and SQLite database connection                  |
| `database.db`        | SQLite database with sample data                                  |
| `templates/`         | Jinja2 HTML templates                                              |
| `static/style.css`   | Stylesheet                                                          |
| `requirements.txt`   | Python dependencies                                                 |

## Main Features

- User registration, login, logout (Flask sessions, hashed passwords)
- Browse and filter events by title, category, date and location
- Event detail page with live participant count
- Register / cancel registration for events (duplicate registration blocked)
- Personal user area listing your registrations
- Protected admin backoffice: create / edit / delete events, manage
  categories and view registered users per event
