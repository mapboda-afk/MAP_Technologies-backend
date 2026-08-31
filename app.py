from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "MAP_Technologies backend is online 🚀"
    })


@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "success": False,
            "message": "No registration data received."
        }), 400

    first_name = data.get("firstName", "").strip()
    last_name = data.get("lastName", "").strip()
    email = data.get("email", "").strip()
    age = data.get("age")
    department = data.get("department", "").strip()

    if not first_name or not last_name or not email or not department:
        return jsonify({
            "success": False,
            "message": "Please complete all required fields."
        }), 400

    return jsonify({
        "success": True,
        "message": f"Welcome to MAP_Technologies, {first_name}! 🚀",
        "student": {
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "age": age,
            "department": department
        }
    })


if __name__ == "__main__":
    app.run()