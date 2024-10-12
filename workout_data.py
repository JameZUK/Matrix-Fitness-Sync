from flask import Flask, jsonify, request
import requests
import os
import json

# API base URL
BASE_URL = "https://apollo.jfit.co"
LOGIN_ENDPOINT = "exerciser/login"
WORKOUTS_ENDPOINT = "exerciser/{exerciser_id}/workouts"

app = Flask(__name__)

# Function to log in using XID
def login(username, password, api_key, debug=False):
    url = f"{BASE_URL}/{LOGIN_ENDPOINT}"
    payload = {
        "username": username,
        "password": password,
        "type": "xid"
    }
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    if debug:
        print(f"Debug: Sending POST request to {url}")
        print(f"Debug: Headers: {headers}")
        print(f"Debug: Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers)

    if debug:
        print(f"Debug: Status Code: {response.status_code}")
        print(f"Debug: Response Text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        return data.get("token"), data.get("id")
    else:
        print(f"Login failed: {response.status_code}")
        return None, None

# Function to fetch workout data from API
def fetch_workouts(token, exerciser_id, api_key, debug=False):
    endpoint = WORKOUTS_ENDPOINT.format(exerciser_id=exerciser_id)
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": api_key
    }

    if debug:
        print(f"Debug: Sending GET request to {url}")
        print(f"Debug: Headers: {headers}")

    response = requests.get(url, headers=headers)

    if debug:
        print(f"Debug: Status Code: {response.status_code}")
        print(f"Debug: Response Text: {response.text}")

    if response.status_code == 200:
        return response.json().get("workouts", [])
    else:
        print(f"Failed to fetch workouts: {response.status_code}")
        return []

# API endpoint to serve workout data to Home Assistant
@app.route('/workout_data', methods=['GET'])
def workout_data():
    # Fetch environment variables and ensure they are available
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    api_key = os.environ.get("API_KEY")
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    if not username or not password or not api_key:
        return jsonify({"error": "Missing credentials"}), 500

    # Log in to the external API
    token, exerciser_id = login(username, password, api_key, debug)

    if token and exerciser_id:
        workouts = fetch_workouts(token, exerciser_id, api_key, debug)
        if workouts:
            return jsonify({"workouts": workouts}), 200
        else:
            return jsonify({"error": "No workouts found"}), 404
    else:
        return jsonify({"error": "Login failed"}), 500

if __name__ == '__main__':
    # Check environment variables at startup and print them
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    print(f"Starting server with the following configuration:")
    print(f"Username: {os.environ.get('USERNAME')}")
    print(f"Password: {'*' * len(os.environ.get('PASSWORD', ''))}")  # Mask password
    print(f"API Key: {'*' * len(os.environ.get('API_KEY', ''))}")    # Mask API key
    print(f"Debug mode: {debug}")

    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=debug)
