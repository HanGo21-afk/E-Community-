import os
import uuid

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)

app.config["UPLOAD_FOLDER"] = os.path.join(
    app.instance_path, "assistance_uploads"
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


app.secret_key = os.getenv("ecommunity-secret-key")


db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "e_community")
)



# =========================
# PUBLIC PAGES
# =========================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/service")
def service():
    return render_template("service.html")


# =========================
# CONTACT MESSAGES
# =========================

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return "Please fill in all required fields.", 400

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO e_community.contact_messages
                    (name, email, subject, message)
                VALUES (%s, %s, %s, %s)
                """,
                (name, email, subject, message)
            )

            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error saving contact message:", err)

            return (
                "Unable to send your message right now. Please try again.",
                500
            )

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/contact-complete")

    return render_template("contact.html")


@app.route("/contact-complete")
def contact_complete():
    return render_template("contact_complete.html")


@app.route("/complete")
def complete():
    return render_template("complete.html")


# =========================
# HEALTH REQUESTS
# =========================

@app.route("/health", methods=["GET", "POST"])
def health():
    if "user_id" not in session:
        return redirect("/signin")

    if request.method == "POST":
        try:
            resident_age = int(request.form.get("resident-age", ""))
        except (TypeError, ValueError):
            return "Please enter a valid resident age.", 400

        resident_name = request.form.get("resident-name", "").strip()
        resident_gender = request.form.get("resident-gender", "").strip()
        resident_contact = request.form.get("resident-contact", "").strip()
        resident_address = request.form.get("resident-address", "").strip()

        service_type = request.form.get("service-type", "").strip()
        preferred_date = request.form.get("preferred-date") or None
        description = request.form.get("health-reason", "").strip()

        symptom_onset = request.form.get("symptom-onset", "").strip() or None
        severity = request.form.get("severity", "").strip() or None
        allergies = request.form.get("allergies", "").strip() or None
        allergy_specify = request.form.get("allergy-specify", "").strip() or None
        medication = request.form.get("medication", "").strip() or None
        medication_specify = request.form.get("medication-specify", "").strip() or None
        existing_illness = request.form.get("existing-illness", "").strip() or None

        senior_citizen = request.form.get("senior-citizen") == "on"
        pwd = request.form.get("pwd") == "on"
        pregnant = request.form.get("pregnant") == "on"
        child = request.form.get("child") == "on"

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO service_requests (
                    user_id, service_type, description,
                    resident_name, resident_age, resident_gender,
                    resident_contact, resident_address, preferred_date,
                    symptom_onset, severity, allergies, allergy_specify,
                    medication, medication_specify, existing_illness,
                    senior_citizen, pwd, pregnant, child
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    session["user_id"], service_type, description,
                    resident_name, resident_age, resident_gender,
                    resident_contact, resident_address, preferred_date,
                    symptom_onset, severity, allergies, allergy_specify,
                    medication, medication_specify, existing_illness,
                    senior_citizen, pwd, pregnant, child
                )
            )

            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error saving health request:", err)
            return "Unable to save the health request. Please try again.", 500

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/complete")

    return render_template("health.html")


# =========================
# ASSISTANCE REQUESTS
# =========================

@app.route("/assistance", methods=["GET", "POST"])
def assistance():
    if "user_id" not in session:
        return redirect("/signin")

    if request.method == "POST":
        assistance_types = request.form.getlist("assistance-type")
        request_reason = request.form.get("request-reason", "").strip()

        applicant_name = request.form.get("applicant-name", "").strip()
        applicant_gender = request.form.get("applicant-gender", "").strip()
        applicant_contact = request.form.get("applicant-contact", "").strip()
        applicant_address = request.form.get("applicant-address", "").strip()

        try:
            applicant_age = int(request.form.get("applicant-age", ""))
            household_members = int(request.form.get("household-members", ""))
        except (ValueError, TypeError):
            return "Please enter valid age and household member numbers.", 400

        if not assistance_types or not request_reason:
            return "Please select an assistance type and provide a reason.", 400

        if applicant_age < 0 or applicant_age > 150 or household_members < 1:
            return "Please enter valid applicant and household information.", 400

        service_type = ", ".join(assistance_types)
        amount_requested = request.form.get("amount-requested", "").strip() or None
        date_needed = request.form.get("date-needed") or None
        income_source = request.form.get("income-source", "").strip() or None
        monthly_income = request.form.get("monthly-income", "").strip() or None

        supporting_file = request.files.get("supporting-document")
        stored_filename = None
        saved_path = None

        if supporting_file and supporting_file.filename:
            safe_name = secure_filename(supporting_file.filename)

            allowed_extensions = {
                "pdf", "jpg", "jpeg", "png", "doc", "docx"
            }

            if (
                "." not in safe_name
                or safe_name.rsplit(".", 1)[1].lower() not in allowed_extensions
            ):
                return "Unsupported supporting document type.", 400

            extension = safe_name.rsplit(".", 1)[1].lower()
            stored_filename = f"{uuid.uuid4().hex}.{extension}"

            saved_path = os.path.join(
                app.config["UPLOAD_FOLDER"], stored_filename
            )

            supporting_file.save(saved_path)

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO service_requests (
                    user_id, service_type, description,
                    resident_name, resident_age, resident_gender,
                    resident_contact, resident_address,
                    amount_requested, date_needed, household_members,
                    income_source, monthly_income, supporting_document
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s, %s)
                """,
                (
                    session["user_id"], service_type, request_reason,
                    applicant_name, applicant_age, applicant_gender,
                    applicant_contact, applicant_address,
                    amount_requested, date_needed, household_members,
                    income_source, monthly_income, stored_filename
                )
            )

            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error saving assistance request:", err)

            if saved_path and os.path.exists(saved_path):
                os.remove(saved_path)

            return "Unable to save the assistance request. Please try again.", 500

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/complete")

    return render_template("assistance.html")


# =========================
# COMPLAINTS
# =========================

@app.route("/complaint", methods=["GET", "POST"])
def complaint():
    if "user_id" not in session:
        return redirect("/signin")

    if request.method == "POST":
        subject = request.form["complaint-type"]
        description = request.form["complaint-description"]

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO complaints (user_id, subject, description)
                VALUES (%s, %s, %s)
                """,
                (session["user_id"], subject, description)
            )
            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error saving complaint:", err)
            return "Unable to save the complaint. Please try again.", 500

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/complete")

    return render_template("complaint.html")


# =========================
# DOCUMENT REQUESTS
# =========================

@app.route("/req-doc", methods=["GET", "POST"])
def req_doc():
    if "user_id" not in session:
        return redirect("/signin")

    if request.method == "POST":
        document_type = request.form["documentType"]
        purpose = request.form["purpose"]

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO document_requests
                    (user_id, document_type, purpose)
                VALUES (%s, %s, %s)
                """,
                (session["user_id"], document_type, purpose)
            )
            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error saving document request:", err)
            return "Unable to save the document request. Please try again.", 500

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/complete")

    return render_template("req-doc.html")


@app.route("/track")
def track():
    if "user_id" not in session:
        return redirect("/signin")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, document_type, purpose, request_date, status
            FROM document_requests
            WHERE user_id = %s
            ORDER BY request_date DESC
            """,
            (session["user_id"],)
        )

        requests_list = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error loading document requests:", err)
        return "Unable to load document requests. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return render_template("track.html", requests=requests_list)


# =========================
# SIGN IN AND LOGOUT
# =========================

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        contact_info = request.form["contact_info"]
        password = request.form["password"]

        cursor = None

        try:
            db.reconnect(attempts=3, delay=1)
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT * FROM users
                WHERE (email = %s OR contact_info = %s)
                  AND password = %s
                """,
                (contact_info, contact_info, password)
            )

            user = cursor.fetchone()

        except mysql.connector.Error as err:
            print("Error signing in:", err)
            return "Unable to sign in right now. Please try again.", 500

        finally:
            if cursor is not None:
                cursor.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")

            return redirect("/")

        return "Invalid email/contact number or password."

    return render_template("signin.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/signin")


# =========================
# ADMIN DASHBOARD
# =========================

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    return render_template("admin.html")


# =========================
# ADMIN DOCUMENTS
# =========================

@app.route("/admin/documents")
def admin_documents():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                document_requests.id,
                document_requests.document_type,
                document_requests.purpose,
                document_requests.request_date,
                document_requests.status,
                users.first_name,
                users.last_name,
                users.email,
                users.contact_info
            FROM document_requests
            LEFT JOIN users
                ON document_requests.user_id = users.id
            ORDER BY document_requests.request_date DESC
            """
        )

        requests_list = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error loading document requests:", err)
        return "Unable to load document requests. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_documents.html",
        requests=requests_list
    )


@app.route("/admin/documents/<int:request_id>/<action>", methods=["POST"])
def update_document_status(request_id, action):
    if session.get("role") != "admin":
        return redirect("/")

    if action == "approve":
        new_status = "Approved"
    elif action == "reject":
        new_status = "Rejected"
    else:
        return "Invalid document action.", 400

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE document_requests
            SET status = %s
            WHERE id = %s
            """,
            (new_status, request_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            return "Document request not found.", 404

    except mysql.connector.Error as err:
        db.rollback()
        print("Error updating document status:", err)
        return "Unable to update the document request. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return redirect("/admin/documents")


# =========================
# ADMIN HEALTH REQUESTS
# =========================

@app.route("/admin/health")
def admin_health():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id, user_id, service_type, description,
                request_date, status, resident_name, resident_age,
                resident_gender, resident_contact, resident_address,
                preferred_date, symptom_onset, severity,
                allergies, allergy_specify, medication,
                medication_specify, existing_illness,
                senior_citizen, pwd, pregnant, child
            FROM service_requests
            WHERE service_type IN (
                'general-checkup',
                'vaccination',
                'medical-consultation',
                'maternal-child'
            )
            ORDER BY request_date DESC
            """
        )

        health_requests = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error loading health requests:", err)
        return "Unable to load health requests. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_health.html",
        requests=health_requests
    )


@app.route("/admin/health/<int:request_id>/<action>", methods=["POST"])
def update_health_status(request_id, action):
    if session.get("role") != "admin":
        return redirect("/")

    if action == "approve":
        new_status = "Approved"
    elif action == "reject":
        new_status = "Rejected"
    else:
        return "Invalid health request action.", 400

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE service_requests
            SET status = %s
            WHERE id = %s
              AND service_type IN (
                  'general-checkup',
                  'vaccination',
                  'medical-consultation',
                  'maternal-child'
              )
            """,
            (new_status, request_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            return "Health request not found.", 404

    except mysql.connector.Error as err:
        db.rollback()
        print("Error updating health status:", err)
        return "Unable to update the health request. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return redirect("/admin/health")


# =========================
# ADMIN ASSISTANCE REQUESTS
# =========================

@app.route("/admin/assistance")
def admin_assistance():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                service_type,
                description,
                request_date,
                status,
                resident_name,
                resident_age,
                resident_gender,
                resident_contact,
                resident_address,
                amount_requested,
                date_needed,
                household_members,
                income_source,
                monthly_income,
                supporting_document
            FROM service_requests
            WHERE service_type LIKE '%assistance%'
            ORDER BY request_date DESC
            """
        )

        assistance_requests = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error loading assistance requests:", err)
        return "Unable to load assistance requests. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_assistance.html",
        requests=assistance_requests
    )


@app.route(
    "/admin/assistance/<int:request_id>/<action>",
    methods=["POST"]
)
def update_assistance_status(request_id, action):
    if session.get("role") != "admin":
        return redirect("/")

    if action == "approve":
        new_status = "Approved"
    elif action == "reject":
        new_status = "Rejected"
    else:
        return "Invalid assistance request action.", 400

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE service_requests
            SET status = %s
            WHERE id = %s
              AND service_type LIKE '%assistance%'
            """,
            (new_status, request_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            return "Assistance request not found.", 404

    except mysql.connector.Error as err:
        db.rollback()
        print("Error updating assistance status:", err)
        return "Unable to update the assistance request. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return redirect("/admin/assistance")


# =========================
# ADMIN COMPLAINTS
# =========================

@app.route("/admin/complaints")
def admin_complaints():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                complaints.id,
                complaints.user_id,
                complaints.subject,
                complaints.description,
                complaints.complaint_date,
                complaints.status,
                users.first_name,
                users.last_name,
                users.email,
                users.contact_info
            FROM complaints
            LEFT JOIN users
                ON complaints.user_id = users.id
            ORDER BY complaints.complaint_date DESC
            """
        )

        complaints = cursor.fetchall()

    except mysql.connector.Error as err:
        print("Error loading complaints:", err)
        return "Unable to load complaints. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_complaints.html",
        complaints=complaints
    )


@app.route(
    "/admin/complaints/<int:complaint_id>/<action>",
    methods=["POST"]
)
def update_complaint_status(complaint_id, action):
    if session.get("role") != "admin":
        return redirect("/")

    if action == "approve":
        new_status = "Approved"
    elif action == "reject":
        new_status = "Rejected"
    else:
        return "Invalid complaint action.", 400

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE complaints
            SET status = %s
            WHERE id = %s
            """,
            (new_status, complaint_id)
        )

        db.commit()

        if cursor.rowcount == 0:
            return "Complaint not found.", 404

    except mysql.connector.Error as err:
        db.rollback()
        print("Error updating complaint status:", err)
        return "Unable to update the complaint. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return redirect("/admin/complaints")



# =========================
# ADMIN CONTACT MESSAGES
# =========================

@app.route("/admin/messages")
def admin_messages():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                name,
                email,
                subject,
                message,
                status,
                message_date
            FROM e_community.contact_messages
            ORDER BY message_date DESC
            """
        )

        messages = cursor.fetchall()

        # Finish the read transaction and release its table locks.
        db.commit()

    except mysql.connector.Error as err:
        db.rollback()
        print("Error loading contact messages:", err)

        return (
            "Unable to load contact messages. "
            "Check the VS Code terminal for the error.",
            500
        )

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_messages.html",
        messages=messages
    )
    

# =========================
# UPDATE CONTACT MESSAGE STATUS
# =========================

@app.route(
    "/admin/messages/<int:message_id>/<action>",
    methods=["POST"]
)
def update_contact_message_status(message_id, action):
    if session.get("role") != "admin":
        return redirect("/")

    if action == "read":
        new_status = "Read"
    elif action == "resolve":
        new_status = "Resolved"
    else:
        return "Invalid contact message action.", 400

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor()

        cursor.execute(
            """
            UPDATE e_community.contact_messages
            SET status = %s
            WHERE id = %s
            """,
            (new_status, message_id)
        )

        if cursor.rowcount == 0:
            db.rollback()
            return "Contact message not found.", 404

        db.commit()

    except mysql.connector.Error as err:
        db.rollback()
        print("Error updating contact message status:", err)
        return "Unable to update the message status. Please try again.", 500

    finally:
        if cursor is not None:
            cursor.close()

    return redirect("/admin/messages")




# =========================
# REGISTRATION
# =========================


# =========================
# ADMIN RESIDENTS
# =========================

@app.route("/admin/residents")
def admin_residents():
    if session.get("role") != "admin":
        return redirect("/")

    cursor = None

    try:
        db.reconnect(attempts=3, delay=1)
        cursor = db.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT
                id,
                first_name,
                last_name,
                middle_name,
                suffix,
                address,
                email,
                contact_info,
                role
            FROM e_community.users
            WHERE role IS NULL OR role <> 'admin'
            ORDER BY last_name ASC, first_name ASC
            """
        )

        residents = cursor.fetchall()

        # Release the read transaction after fetching the records.
        db.commit()

    except mysql.connector.Error as err:
        db.rollback()
        print("Error loading residents:", err)
        return (
            "Unable to load residents. Please check the VS Code terminal.",
            500
        )

    finally:
        if cursor is not None:
            cursor.close()

    return render_template(
        "admin_residents.html",
        residents=residents
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["frst-name"]
        last_name = request.form["lst-name"]
        middle_name = request.form.get("mid-name")
        suffix = request.form.get("sfx")
        address = request.form["address"]
        contact_info = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm-password"]

        valid_id = request.files["valid-id"]
        proof_of_residency = request.files["proof-residency"]

        if password != confirm_password:
            return "Passwords do not match."

        cursor = None

        try:
            cursor = db.cursor()

            cursor.execute(
                """
                INSERT INTO users (
                    first_name, last_name, middle_name, suffix,
                    address, email, contact_info, password,
                    valid_id, proof_of_residency
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    first_name,
                    last_name,
                    middle_name,
                    suffix,
                    address,
                    contact_info,
                    contact_info,
                    password,
                    valid_id.filename,
                    proof_of_residency.filename
                )
            )

            db.commit()

        except mysql.connector.Error as err:
            db.rollback()
            print("Error registering user:", err)
            return (
                "Unable to register. Please check your information "
                "and try again.",
                500
            )

        finally:
            if cursor is not None:
                cursor.close()

        return redirect("/signin")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
