from flask import Flask, render_template, request, redirect, session, url_for, flash
from datetime import date, time
import os

from models import db, create_tables, User, Category, Event, Registration

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-before-submission")


@app.before_request
def before_request():
    db.connect(reuse_if_open=True)


@app.after_request
def after_request(response):
    if not db.is_closed():
        db.close()
    return response


def current_user():
    if "user_id" in session:
        return User.get_or_none(User.id == session["user_id"])
    return None


def admin_required():
    user = current_user()
    if not user or not user.is_admin:
        return redirect(url_for("index"))
    return None


@app.route("/")
def index():
    events = Event.select().order_by(Event.date.desc()).limit(3)
    return render_template("index.html", events=events, user=current_user())


@app.route("/events")
def events():
    search = request.args.get("search", "")
    category_id = request.args.get("category", "")
    event_date = request.args.get("date", "")
    location = request.args.get("location", "")

    query = Event.select()

    if search:
        query = query.where(Event.title.contains(search))

    if category_id:
        query = query.where(Event.category == category_id)

    if event_date:
        query = query.where(Event.date == event_date)

    if location:
        query = query.where(Event.location.contains(location))

    query = query.order_by(Event.date.asc(), Event.time.asc())
    categories = Category.select()

    return render_template(
        "events.html",
        events=query,
        categories=categories,
        search=search,
        selected_category=category_id,
        event_date=event_date,
        location=location,
        user=current_user()
    )


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        return redirect(url_for("events"))

    user = current_user()

    participants = Registration.select().where(
        Registration.event == event
    ).count()

    registered = False

    if user:
        registered = Registration.get_or_none(
            (Registration.user == user) &
            (Registration.event == event)
        ) is not None

    return render_template(
        "event_detail.html",
        event=event,
        participants=participants,
        registered=registered,
        user=user
    )


@app.route("/events/<int:event_id>/register", methods=["POST"])
def register_event(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = current_user()
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        return redirect(url_for("events"))

    participants = Registration.select().where(
        Registration.event == event
    ).count()

    if participants >= event.max_participants:
        flash("This event is full.", "error")
        return redirect(url_for("event_detail", event_id=event.id))

    _, created = Registration.get_or_create(user=user, event=event)

    if created:
        flash("You have successfully registered for this event!", "success")
    else:
        flash("You are already registered for this event.", "info")

    return redirect(url_for("event_detail", event_id=event.id))


@app.route("/events/<int:event_id>/cancel", methods=["POST"])
def cancel_registration(event_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = current_user()
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        return redirect(url_for("user_area"))

    Registration.delete().where(
        (Registration.user == user) &
        (Registration.event == event)
    ).execute()

    flash("Registration cancelled.", "info")
    return redirect(url_for("user_area"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        existing_user = User.get_or_none(
            (User.username == username) |
            (User.email == email)
        )

        if existing_user:
            flash("Username or email already exists.", "error")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)
        user.save()

        flash("Account created successfully. You can now login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html", user=current_user())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.get_or_none(User.username == username)

        if user and user.check_password(password):
            session["user_id"] = user.id
            flash("Welcome back, " + user.username + "!", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", user=current_user())


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/user-area")
def user_area():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user = current_user()

    registrations = Registration.select().where(
        Registration.user == user
    )

    return render_template(
        "user_area.html",
        registrations=registrations,
        user=user
    )


# ─── Backoffice ────────────────────────────────────────────────────────────────

@app.route("/admin/events")
def admin_events():
    guard = admin_required()
    if guard:
        return guard

    events = Event.select()

    return render_template(
        "admin_events.html",
        events=events,
        user=current_user()
    )


@app.route("/admin/events/create", methods=["GET", "POST"])
def admin_create_event():
    guard = admin_required()
    if guard:
        return guard

    categories = Category.select()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin_event_form.html", categories=categories, user=current_user())

        Event.create(
            title=title,
            short_description=request.form.get("short_description", "").strip(),
            description=request.form.get("description", "").strip(),
            date=request.form["date"],
            time=request.form["time"],
            location=request.form.get("location", "").strip(),
            organizer=request.form.get("organizer", "").strip(),
            max_participants=request.form.get("max_participants", 30),
            category=request.form["category"]
        )

        flash("Event created successfully.", "success")
        return redirect(url_for("admin_events"))

    return render_template(
        "admin_event_form.html",
        categories=categories,
        user=current_user(),
        event=None
    )


@app.route("/admin/events/<int:event_id>/edit", methods=["GET", "POST"])
def admin_edit_event(event_id):
    guard = admin_required()
    if guard:
        return guard

    event = Event.get_or_none(Event.id == event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin_events"))

    categories = Category.select()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Title is required.", "error")
            return render_template("admin_event_form.html", categories=categories, event=event, user=current_user())

        event.title = title
        event.short_description = request.form.get("short_description", "").strip()
        event.description = request.form.get("description", "").strip()
        event.date = request.form["date"]
        event.time = request.form["time"]
        event.location = request.form.get("location", "").strip()
        event.organizer = request.form.get("organizer", "").strip()
        event.max_participants = request.form.get("max_participants", 30)
        event.category = request.form["category"]
        event.save()

        flash("Event updated successfully.", "success")
        return redirect(url_for("admin_events"))

    return render_template(
        "admin_event_form.html",
        categories=categories,
        event=event,
        user=current_user()
    )


@app.route("/admin/events/<int:event_id>/delete", methods=["POST"])
def admin_delete_event(event_id):
    guard = admin_required()
    if guard:
        return guard

    event = Event.get_or_none(Event.id == event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin_events"))

    # Delete all registrations for this event first to avoid orphan rows
    Registration.delete().where(Registration.event == event).execute()
    event.delete_instance()

    flash("Event deleted.", "info")
    return redirect(url_for("admin_events"))


@app.route("/admin/events/<int:event_id>/registrants")
def admin_event_registrants(event_id):
    guard = admin_required()
    if guard:
        return guard

    event = Event.get_or_none(Event.id == event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin_events"))

    registrations = (
        Registration
        .select(Registration, User)
        .join(User)
        .where(Registration.event == event)
    )

    return render_template(
        "admin_event_registrants.html",
        event=event,
        registrations=registrations,
        user=current_user()
    )


@app.route("/admin/categories")
def admin_categories():
    guard = admin_required()
    if guard:
        return guard

    categories = Category.select()

    return render_template(
        "admin_categories.html",
        categories=categories,
        user=current_user()
    )


@app.route("/admin/categories/create", methods=["POST"])
def admin_create_category():
    guard = admin_required()
    if guard:
        return guard

    name = request.form.get("name", "").strip()
    if not name:
        flash("Category name is required.", "error")
        return redirect(url_for("admin_categories"))

    _, created = Category.get_or_create(name=name)
    if created:
        flash("Category created.", "success")
    else:
        flash("Category already exists.", "info")

    return redirect(url_for("admin_categories"))


@app.route("/admin/categories/<int:category_id>/delete", methods=["POST"])
def admin_delete_category(category_id):
    guard = admin_required()
    if guard:
        return guard

    category = Category.get_or_none(Category.id == category_id)
    if not category:
        flash("Category not found.", "error")
        return redirect(url_for("admin_categories"))

    if category.events.count() > 0:
        flash("Cannot delete a category that has events assigned to it.", "error")
        return redirect(url_for("admin_categories"))

    category.delete_instance()
    flash("Category deleted.", "info")
    return redirect(url_for("admin_categories"))


# ─── Seed & Entry Point ────────────────────────────────────────────────────────

def seed_data():
    if Category.select().count() == 0:
        workshop = Category.create(name="Workshop")
        study = Category.create(name="Study")
        talk = Category.create(name="Talk")
        sports = Category.create(name="Sports")
        culture = Category.create(name="Culture")

        Event.create(
            title="Intro to Flask Apps",
            short_description="Build a small web application with routes, templates and a database.",
            description="A practical workshop where students learn how to transform a simple HTML prototype into a real Flask web application.",
            date=date(2026, 5, 21),
            time=time(14, 30),
            location="Lab 2.4",
            organizer="Web Technologies Club",
            max_participants=30,
            category=workshop
        )

        Event.create(
            title="Database Exam Study Group",
            short_description="Prepare for the database exam with practical exercises.",
            description="A study group focused on SQLite, Peewee models and database exercises.",
            date=date(2026, 5, 18),
            time=time(10, 0),
            location="Library Room B",
            organizer="Student Study Group",
            max_participants=20,
            category=study
        )

        Event.create(
            title="Careers in Web Development",
            short_description="Alumni share advice about internships, portfolios and job interviews.",
            description="A talk about careers in web development, with practical advice from former students.",
            date=date(2026, 5, 23),
            time=time(16, 0),
            location="Auditorium A",
            organizer="Career Office",
            max_participants=60,
            category=talk
        )

        Event.create(
            title="Friday Futsal Meetup",
            short_description="A casual futsal match open to all students.",
            description="A relaxed sports activity where students can meet and play futsal together.",
            date=date(2026, 5, 29),
            time=time(18, 0),
            location="Campus Court",
            organizer="Sports Club",
            max_participants=14,
            category=sports
        )

    if User.select().where(User.username == "admin").count() == 0:
        admin = User(
            username="admin",
            email="admin@meethub.com",
            is_admin=True
        )
        admin.set_password("admin123")
        admin.save()


if __name__ == "__main__":
    create_tables()

    db.connect(reuse_if_open=True)
    seed_data()
    db.close()

    app.run(debug=False)
