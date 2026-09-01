from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client, Client
import os
import logging


# =========================================================
# APP SETUP
# =========================================================

app = Flask(__name__)

# Allow the Vercel frontend to communicate with this backend.
# We are not using cookies here, so credentials are not required.
CORS(
    app,
    resources={r"/api/*": {"origins": "*"}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("map-technologies")


# =========================================================
# SUPABASE CONNECTION
# =========================================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")


if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL is missing. Add it to Render Environment Variables."
    )


if not SUPABASE_PUBLISHABLE_KEY:
    raise RuntimeError(
        "SUPABASE_PUBLISHABLE_KEY is missing. Add it to Render Environment Variables."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_PUBLISHABLE_KEY
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_error_details(error):
    """
    Safely extract useful information from Supabase/other errors.
    """
    message = str(error)

    status = getattr(error, "status", None)
    code = getattr(error, "code", None)

    return message, status, code


def json_error(message, status_code=400, error_code=None):
    """
    Return errors in one consistent JSON format.
    """
    response = {
        "success": False,
        "message": message
    }

    if error_code:
        response["code"] = error_code

    return jsonify(response), status_code


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "MAP_Technologies backend is online 🚀"
    })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "healthy",
        "service": "MAP_Technologies backend"
    })


# =========================================================
# REGISTER
# =========================================================

@app.route("/api/register", methods=["POST", "OPTIONS"])
def register():

    # Handle browser CORS preflight request
    if request.method == "OPTIONS":
        return "", 204

    logger.info("Registration request received.")

    data = request.get_json(silent=True)

    if not data:
        logger.warning("Registration failed: no JSON data received.")
        return json_error(
            "No registration data received.",
            400,
            "NO_DATA"
        )

    # -----------------------------------------------------
    # GET FORM DATA
    # -----------------------------------------------------

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
        return json_error(
            "First name is required.",
            400,
            "FIRST_NAME_REQUIRED"
        )

    if not last_name:
        return json_error(
            "Last name is required.",
            400,
            "LAST_NAME_REQUIRED"
        )

    if not email:
        return json_error(
            "Email is required.",
            400,
            "EMAIL_REQUIRED"
        )

    if not department:
        return json_error(
            "Department is required.",
            400,
            "DEPARTMENT_REQUIRED"
        )

    if age is None or str(age).strip() == "":
        return json_error(
            "Age is required.",
            400,
            "AGE_REQUIRED"
        )

    if len(password) < 8:
        return json_error(
            "Password must contain at least 8 characters.",
            400,
            "PASSWORD_TOO_SHORT"
        )


    # =====================================================
    # SUPABASE SIGNUP
    # =====================================================

    try:

        logger.info(
            "Creating Supabase account for email: %s",
            email
        )

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


        if not user:
            logger.error(
                "Supabase signup returned no user for %s",
                email
            )

            return json_error(
                "Supabase did not create the account.",
                500,
                "USER_CREATION_FAILED"
            )


        logger.info(
            "Registration successful for email: %s",
            email
        )


        return jsonify({
            "success": True,
            "message": "Account created successfully.",
            "emailConfirmationRequired": session is None,
            "user": {
                "id": user.id,
                "email": user.email
            }
        }), 201


    except Exception as error:

        message, error_status, error_code = get_error_details(error)

        logger.exception(
            "SUPABASE REGISTRATION ERROR for %s: %s",
            email,
            message
        )


        # -------------------------------------------------
        # RATE LIMIT
        # -------------------------------------------------

        if error_status == 429:
            return json_error(
                "Too many signup attempts. Please wait a little while and try again.",
                429,
                "RATE_LIMITED"
            )


        # -------------------------------------------------
        # DUPLICATE USER
        # -------------------------------------------------

        lowered_message = message.lower()

        if (
            "already registered" in lowered_message
            or "user already registered" in lowered_message
        ):
            return json_error(
                "An account with this email already exists. Please sign in instead.",
                409,
                "USER_ALREADY_EXISTS"
            )


        # -------------------------------------------------
        # OTHER SUPABASE ERRORS
        # -------------------------------------------------

        return json_error(
            f"Registration failed: {message}",
            400,
            error_code
        )


# =========================================================
# LOGIN
# =========================================================

@app.route("/api/login", methods=["POST", "OPTIONS"])
def login():

    # Handle browser CORS preflight request
    if request.method == "OPTIONS":
        return "", 204

    logger.info("Login request received.")

    data = request.get_json(silent=True)

    if not data:
        return json_error(
            "No login data received.",
            400,
            "NO_DATA"
        )


    email = str(
        data.get("email", "")
    ).strip().lower()

    password = str(
        data.get("password", "")
    )


    # -----------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------

    if not email:
        return json_error(
            "Email is required.",
            400,
            "EMAIL_REQUIRED"
        )

    if not password:
        return json_error(
            "Password is required.",
            400,
            "PASSWORD_REQUIRED"
        )


    # =====================================================
    # SUPABASE LOGIN
    # =====================================================

    try:

        logger.info(
            "Attempting login for email: %s",
            email
        )

        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })


        user = response.user
        session = response.session


        if not user or not session:
            logger.warning(
                "Login failed: Supabase returned no user/session for %s",
                email
            )

            return json_error(
                "Login failed. Please check your email and password.",
                401,
                "LOGIN_FAILED"
            )


        metadata = user.user_metadata or {}

        first_name = metadata.get(
            "first_name",
            "Learner"
        )


        logger.info(
            "Login successful for email: %s",
            email
        )


        return jsonify({
            "success": True,
            "message": "Login successful.",

            "accessToken": session.access_token,

            "user": {
                "id": user.id,
                "email": user.email,
                "firstName": first_name
            }
        }), 200


    except Exception as error:

        message, error_status, error_code = get_error_details(error)

        logger.exception(
            "SUPABASE LOGIN ERROR for %s: %s",
            email,
            message
        )


        # -------------------------------------------------
        # RATE LIMIT
        # -------------------------------------------------

        if error_status == 429:
            return json_error(
                "Too many login attempts. Please wait a little while and try again.",
                429,
                "RATE_LIMITED"
            )


        # -------------------------------------------------
        # INVALID CREDENTIALS
        # -------------------------------------------------

        lowered_message = message.lower()

        if (
            "invalid login credentials" in lowered_message
            or "invalid credentials" in lowered_message
        ):
            return json_error(
                "Invalid email or password.",
                401,
                "INVALID_CREDENTIALS"
            )


        # -------------------------------------------------
        # OTHER AUTH ERRORS
        # -------------------------------------------------

        return json_error(
            f"Login failed: {message}",
            401,
            error_code
        )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/api/logout", methods=["POST", "OPTIONS"])
def logout():

    if request.method == "OPTIONS":
        return "", 204

    return jsonify({
        "success": True,
        "message": "Logout completed on the client."
    })


# =========================================================
# GLOBAL ERROR HANDLER
# =========================================================

@app.errorhandler(Exception)
def handle_unexpected_error(error):

    logger.exception(
        "UNEXPECTED SERVER ERROR: %s",
        str(error)
    )

    return json_error(
        "An unexpected server error occurred. Please try again.",
        500,
        "INTERNAL_SERVER_ERROR"
    )


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )