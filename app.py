import os
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

app = Flask(__name__)
app.secret_key = "replace_this_with_a_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    """Create the SQLite database and required tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            blood_group TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            address TEXT,
            registered_at TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blood_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blood_group TEXT UNIQUE NOT NULL,
            units INTEGER NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS blood_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            units INTEGER NOT NULL,
            phone TEXT,
            email TEXT,
            hospital TEXT,
            city TEXT,
            status TEXT,
            request_date TEXT
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    cursor.execute("SELECT COUNT(*) FROM admin_users")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO admin_users (username, password) VALUES (?, ?)",
            ("admin", "admin123"),
        )

    initial_stock = [
        ("A+", 0),
        ("A-", 0),
        ("B+", 0),
        ("B-", 0),
        ("AB+", 0),
        ("AB-", 0),
        ("O+", 0),
        ("O-", 0),
    ]

    cursor.execute("SELECT blood_group FROM blood_stock")
    existing_groups = {row[0] for row in cursor.fetchall()}

    for blood_group, units in initial_stock:
        if blood_group not in existing_groups:
            cursor.execute(
                "INSERT INTO blood_stock (blood_group, units) VALUES (?, ?)",
                (blood_group, units),
            )

    conn.commit()
    conn.close()

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register_donor():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not blood_group:
            flash("Please enter both name and blood group.", "warning")
            return redirect(url_for("register_donor"))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO donors (
                name, age, gender, blood_group, phone, email, address, registered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                int(age) if age.isdigit() else None,
                gender,
                blood_group,
                phone,
                email,
                address,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()

        flash("Donor registration successful.", "success")
        return redirect(url_for("register_donor"))

    return render_template("register_donor.html")


@app.route("/search", methods=["GET", "POST"])
def search_blood():
    donors = []
    stock = None
    search_group = ""

    if request.method == "POST":
        search_group = request.form.get("blood_group", "").strip()

        if search_group:
            conn = get_db_connection()
            donors = conn.execute(
                "SELECT * FROM donors WHERE blood_group = ?",
                (search_group,),
            ).fetchall()
            stock = conn.execute(
                "SELECT * FROM blood_stock WHERE blood_group = ?",
                (search_group,),
            ).fetchone()
            conn.close()

            if not donors and not stock:
                flash("No matching donors or stock found for this blood group.", "info")
        else:
            flash("Please choose a blood group to search.", "warning")

    return render_template(
        "search_blood.html",
        donors=donors,
        stock=stock,
        search_group=search_group,
    )


@app.route("/request", methods=["GET", "POST"])
def request_blood():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        units = request.form.get("units", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        hospital = request.form.get("hospital", "").strip()
        city = request.form.get("city", "").strip()

        if not name or not blood_group or not units.isdigit():
            flash("Please enter a valid name, blood group, and units.", "warning")
            return redirect(url_for("request_blood"))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO blood_requests (
                name, blood_group, units, phone, email, hospital, city, status, request_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                blood_group,
                int(units),
                phone,
                email,
                hospital,
                city,
                "Pending",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()
        conn.close()

        flash("Blood request submitted successfully.", "success")
        return redirect(url_for("request_blood"))

    return render_template("request_blood.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db_connection()
        admin = conn.execute(
            "SELECT * FROM admin_users WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
        conn.close()

        if admin:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "danger")

    return render_template("admin_login.html")


def admin_required(view):
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Please log in as admin to continue.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    wrapper.__name__ = view.__name__
    return wrapper


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    donors = conn.execute("SELECT * FROM donors ORDER BY registered_at DESC").fetchall()
    requests_list = conn.execute(
        "SELECT * FROM blood_requests ORDER BY request_date DESC"
    ).fetchall()
    stock = conn.execute("SELECT * FROM blood_stock ORDER BY blood_group").fetchall()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        donors=donors,
        requests=requests_list,
        stock=stock,
    )


@app.route("/admin/donors")
@admin_required
def donor_list():
    conn = get_db_connection()
    donors = conn.execute("SELECT * FROM donors ORDER BY registered_at DESC").fetchall()
    conn.close()
    return render_template("donor_list.html", donors=donors)

@app.route("/view_requests")
@admin_required
def view_requests():
    conn = get_db_connection()
    requests_data = conn.execute(
        "SELECT id, name, blood_group, hospital, phone, city, units, request_date, status FROM blood_requests ORDER BY request_date DESC"
    ).fetchall()
    conn.close()

    return render_template("view_requests.html", requests=requests_data)

@app.route("/admin/stock", methods=["GET", "POST"])
@admin_required
def blood_stock():
    if request.method == "POST":
        blood_group = request.form.get("blood_group", "").strip()
        units = request.form.get("units", "").strip()

        if not blood_group or not units.isdigit():
            flash("Please enter a valid group and units number.", "warning")
            return redirect(url_for("blood_stock"))

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT * FROM blood_stock WHERE blood_group = ?", (blood_group,)
        ).fetchone()

        if existing:
            conn.execute(
                "UPDATE blood_stock SET units = units + ? WHERE blood_group = ?",
                (int(units), blood_group),
            )
        else:
            conn.execute(
                "INSERT INTO blood_stock (blood_group, units) VALUES (?, ?)",
                (blood_group, int(units)),
            )

        conn.commit()
        conn.close()
        flash("Blood stock updated successfully.", "success")
        return redirect(url_for("blood_stock"))

    conn = get_db_connection()
    stock = conn.execute("SELECT * FROM blood_stock ORDER BY blood_group").fetchall()
    conn.close()
    return render_template("blood_stock.html", stock=stock)


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)