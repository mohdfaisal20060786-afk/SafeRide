from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db

app = Flask(__name__)
init_db()

# Session secret key
app.secret_key = "saferide_secret_key_2026"


# =========================
# HOME
# =========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/privacy-policy")
def privacy_policy():
    return render_template("privacy-policy.html")

@app.route("/current-location")
def current_location():
    if "user_id" not in session:
        return redirect("/login")

    return render_template("current_location.html")

# =========================
# PROFILE
# =========================

@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT id, name, email, phone
            FROM users
            WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()

        if not user:
            return "User not found", 404

        return render_template(
            "profile.html",
            user=user
        )

    except Exception as error:

        return f"Profile Error: {error}", 500

    finally:

        cursor.close()
        connection.close()
        
# =========================
# VEHICLE
# =========================

@app.route("/vehicle", methods=["GET", "POST"])
def vehicle():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    if request.method == "POST":

        vehicle_number = request.form["vehicle_number"]
        vehicle_model = request.form["vehicle_model"]
        vehicle_color = request.form["vehicle_color"]

        try:
            cursor.execute("""
                INSERT INTO vehicles
                (user_id, vehicle_number, vehicle_model, vehicle_color)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                vehicle_number,
                vehicle_model,
                vehicle_color
            ))

            connection.commit()

        except Exception as error:

            connection.rollback()
            cursor.close()
            connection.close()

            return f"Vehicle Error: {error}"

    cursor.execute("""
        SELECT vehicle_number, vehicle_model, vehicle_color
        FROM vehicles
        WHERE user_id = %s
    """, (user_id,))

    vehicle_data = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template(
        "vehicle.html",
        vehicle=vehicle_data
    )
# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        # Password ko hash karna
        password_hash = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO users (name, email, phone, password)
        VALUES (%s, %s, %s, %s)
        """

        try:

            cursor.execute(
                query,
                (
                    name,
                    email,
                    phone,
                    password_hash
                )
            )

            connection.commit()

        except Exception as error:

            connection.rollback()

            cursor.close()
            connection.close()

            return f"Registration Error: {error}"

        cursor.close()
        connection.close()

        return redirect("/login")

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        
        cursor = connection.cursor()

        query = """
        SELECT *
        FROM users
        WHERE email = %s
        """

        cursor.execute(
            query,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        # Password verify
        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        else:

            return "Invalid Email or Password"

    return render_template("login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user_name=session["user_name"]
    )


# =========================
# ACCIDENT DETECTION
# =========================

@app.route("/accident")
def accident():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("accident.html")


# =========================
# GET LOCATION
# =========================

@app.route("/get-location")
def get_location():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("location.html")


# =========================
# SAVE ACCIDENT
# =========================

@app.route("/save-accident", methods=["POST"])
def save_accident():

    if "user_id" not in session:

        return jsonify({
            "success": False,
            "message": "User not logged in."
        }), 401

    data = request.get_json()

    if not data:

        return jsonify({
            "success": False,
            "message": "No location data received."
        }), 400

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:

        return jsonify({
            "success": False,
            "message": "Latitude or longitude missing."
        }), 400

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO accidents
    (user_id, latitude, longitude, status)
    VALUES (%s, %s, %s, %s)
    """

    try:

        cursor.execute(
            query,
            (
                user_id,
                latitude,
                longitude,
                "Detected"
            )
        )

        connection.commit()

    except Exception as error:
        print("SAVE ACCIDENT DATABASE ERROR:", error)

        connection.rollback()

        cursor.close()
        connection.close()

        return jsonify({
            "success": False,
            "message": f"Database Error: {error}"
        }), 500

    cursor.close()
    connection.close()

    return jsonify({
        "success": True,
        "message": "Accident details saved successfully!"
    })


# =========================
# EMERGENCY CONTACTS
# =========================

@app.route("/contacts", methods=["GET", "POST"])
def contacts():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    # Add contact
    if request.method == "POST":

        contact_name = request.form["contact_name"]
        phone = request.form["phone"]
        relation_name = request.form["relation_name"]

        query = """
        INSERT INTO emergency_contacts
        (user_id, contact_name, phone, relation_name)
        VALUES (%s, %s, %s, %s)
        """

        try:

            cursor.execute(
                query,
                (
                    user_id,
                    contact_name,
                    phone,
                    relation_name
                )
            )

            connection.commit()

        except Exception as error:

            connection.rollback()

            cursor.close()
            connection.close()

            return f"Contact Error: {error}"

    # Get contacts
    query = """
    SELECT *
    FROM emergency_contacts
    WHERE user_id = %s
    ORDER BY id DESC
    """

    cursor.execute(
        query,
        (user_id,)
    )

    contacts_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "contacts.html",
        contacts=contacts_list
    )


# =========================
# ACCIDENT HISTORY
# =========================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
SELECT
    id,
    user_id,
    latitude,
    longitude,
    status,
    accident_time AT TIME ZONE 'UTC'
                    AT TIME ZONE 'Asia/Kolkata' AS accident_time
FROM accidents
WHERE user_id = %s
ORDER BY accident_time DESC
"""

    cursor.execute(
        query,
        (user_id,)
    )

    accidents_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "history.html",
        accidents=accidents_list
    )


# =========================
# EMERGENCY ALERT
# =========================

@app.route("/send-alert")
def send_alert():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    # Latest accident
    accident_query = """
    SELECT *
    FROM accidents
    WHERE user_id = %s
    ORDER BY id DESC
    LIMIT 1
    """

    cursor.execute(
        accident_query,
        (user_id,)
    )

    accident_data = cursor.fetchone()

    if not accident_data:

        cursor.close()
        connection.close()

        return "No accident record found."


    # Emergency contacts
    contact_query = """
    SELECT *
    FROM emergency_contacts
    WHERE user_id = %s
    """

    cursor.execute(
        contact_query,
        (user_id,)
    )

    contacts_list = cursor.fetchall()

    if not contacts_list:

        cursor.close()
        connection.close()

        return "No emergency contacts found."


    latitude = accident_data["latitude"]
    longitude = accident_data["longitude"]

    maps_link = (
        "https://www.google.com/maps?q="
        + str(latitude)
        + ","
        + str(longitude)
    )


    # Emergency message
    message = (
        "EMERGENCY ALERT!\n\n"
        "An accident has been detected.\n\n"
        "Accident Location:\n"
        + maps_link
        + "\n\n"
        "Please provide immediate assistance."
    )


    # Save alert for every contact
    for contact in contacts_list:

        alert_query = """
        INSERT INTO emergency_alerts
        (accident_id, user_id, contact_id, message, alert_status)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            alert_query,
            (
                accident_data["id"],
                user_id,
                contact["id"],
                message,
                "Generated"
            )
        )

    connection.commit()

    cursor.close()
    connection.close()


    return render_template(
        "alert.html",
        message=message,
        contacts=contacts_list,
        status="Emergency alert generated successfully"
    )
    # =========================
# CONTACT FORM
# =========================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message = request.form.get("message")

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
            INSERT INTO contact_messages
            (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (name, email, subject, message)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return """
        <html>
        <head>
            <title>Message Sent - SafeRide</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding-top: 100px;
                    background: #f5f5f5;
                }

                .box {
                    background: white;
                    max-width: 500px;
                    margin: auto;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                }

                h1 {
                    color: #e63946;
                }

                a {
                    display: inline-block;
                    margin-top: 20px;
                    padding: 12px 25px;
                    background: #e63946;
                    color: white;
                    text-decoration: none;
                    border-radius: 8px;
                }
            </style>
        </head>

        <body>

            <div class="box">

                <h1>✅ Message Sent!</h1>

                <p>
                    Thank you for contacting SafeRide.
                    Your message has been received successfully.
                </p>

                <a href="/">
                    Back to Home
                </a>

            </div>

        </body>
        </html>
        """

    return redirect("/")
# =========================
# DELETE ACCOUNT
# =========================

@app.route("/delete-account", methods=["POST"])
def delete_account():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Delete emergency alerts
        cursor.execute("""
            DELETE FROM emergency_alerts
            WHERE user_id = %s
        """, (user_id,))

        # Delete accidents
        cursor.execute("""
            DELETE FROM accidents
            WHERE user_id = %s
        """, (user_id,))

        # Delete emergency contacts
        cursor.execute("""
            DELETE FROM emergency_contacts
            WHERE user_id = %s
        """, (user_id,))

        # Delete vehicles
        cursor.execute("""
            DELETE FROM vehicles
            WHERE user_id = %s
        """, (user_id,))

        # Delete user
        cursor.execute("""
            DELETE FROM users
            WHERE id = %s
        """, (user_id,))

        connection.commit()

        session.clear()

        return redirect("/")

    except Exception as error:

        connection.rollback()

        return f"Account deletion error: {error}", 500

    finally:

        cursor.close()
        connection.close()


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
        ssl_context="adhoc"
    )