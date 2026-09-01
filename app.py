from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client
import os


app = Flask(__name__)

CORS(app)


# =========================================================
# SUPABASE CONNECTION
# =========================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get(
    "SUPABASE_PUBLISHABLE_KEY"
)


if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
    raise RuntimeError(
        "Supabase environment variables are missing."
    )


supabase = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "success": True,
        "message": "MAP_Technologies backend is online 🚀"
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health")
def health():

    return jsonify({
        "success": True,
        "status": "healthy"
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "No registration data received."
        }), 400


    first_name = str(
        data.get("firstName", "")
    ).strip()


    last_name = str(
        data.get("lastName", "")
    ).strip()


    email = str(
        data.get("email", "")
    ).strip().lower()


    age = data.get("age")


    department = str(
        data.get("department", "")
    ).strip()


    password = str(
        data.get("password", "")
    )


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not first_name:
        return jsonify({
            "success": False,
            "message": "First name is required."
        }), 400


    if not last_name:
        return jsonify({
            "success": False,
            "message": "Last name is required."
        }), 400


    if not email:
        return jsonify({
            "success": False,
            "message": "Email is required."
        }), 400


    if not department:
        return jsonify({
            "success": False,
            "message": "Department is required."
        }), 400


    if not age:
        return jsonify({
            "success": False,
            "message": "Age is required."
        }), 400


    if len(password) < 8:
        return jsonify({
            "success": False,
            "message": "Password must contain at least 8 characters."
        }), 400


    try:

        response = supabase.auth.sign_up({
            "email": email,

            "password": password,

            "options": {
                "data": {
                    "first_name": first_name,
                    "last_name": last_name,
                    "age": age,
                    "department": department
                }
            }
        })


        user = response.user
        session = response.session


        return jsonify({

            "success": True,

            "message":
                "Account created successfully.",

            "emailConfirmationRequired":
                session is None,

            "user": {

                "id":
                    user.id if user else None,

                "email":
                    user.email if user else email

            }

        }), 201


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 400


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({
            "success": False,
            "message": "No login data received."
        }), 400


    email = str(
        data.get("email", "")
    ).strip().lower()


    password = str(
        data.get("password", "")
    )


    if not email or not password:

        return jsonify({
            "success": False,
            "message": "Email and password are required."
        }), 400


    try:

        response = (
            supabase
            .auth
            .sign_in_with_password({
                "email": email,
                "password": password
            })
        )


        user = response.user
        session = response.session


        if not user or not session:

            return jsonify({
                "success": False,
                "message": "Login failed."
            }), 401


        metadata = user.user_metadata or {}


        first_name = metadata.get(
            "first_name",
            "Learner"
        )


        return jsonify({

            "success": True,

            "message":
                "Login successful.",

            "accessToken":
                session.access_token,

            "refreshToken":
                session.refresh_token,

            "user": {

                "id":
                    user.id,

                "email":
                    user.email,

                "firstName":
                    first_name

            }

        })


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                str(error)

        }), 401


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST"])
def logout():

    return jsonify({

        "success": True,

        "message":
            "Logout completed on the client."

    })


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )