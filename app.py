from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify({
        "success": True,
        "message": "MAP_Technologies backend is online 🚀"
    })


@app.route("/api/health")
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


if __name__ == "__main__":
    app.run()