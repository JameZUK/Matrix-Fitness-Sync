from flask import Flask, jsonify
import os
import requests

app = Flask(__name__)

# Load settings from environment variables or passed arguments
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
API_KEY = os.environ.get('API_KEY')
DEBUG = os.environ.get('DEBUG', False)

BASE_URL = "https://apollo.jfit.co"
LOGIN_ENDPOINT = "exerciser/login"
WORKOUTS_ENDPOINT = "exerciser/{exerciser_id}/workouts"

# Function to log in using XID
def login():
    url = f"{BASE_URL}/{LOGIN_ENDPOINT}"
    payload = {
        "username": USERNAME,
        "password": PASSWORD,
        "type": "xid"
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        return data.get("token"), data.get("id")
    else:
        return None, None

# REST API endpoint for Home Assistant to call
@app.route("/api/workouts", methods=["GET"])
def workouts_endpoint():
    token, exerciser_id = login()
    if token and exerciser_id:
        # Fetch workouts
        url = f"{BASE_URL}/{WORKOUTS_ENDPOINT.format(exerciser_id=exerciser_id)}"
        headers = {
            "Authorization": f"Bearer {token}",
            "x-api-key": API_KEY
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            workouts = response.json().get("workouts", [])
            return jsonify({
                "state": len(workouts),
                "attributes": {"workouts": workouts}
            })
    return jsonify({"error": "Failed to fetch workouts"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

