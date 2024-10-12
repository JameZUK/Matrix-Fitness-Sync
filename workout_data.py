from flask import Flask, jsonify, request
import requests
import json
import argparse

# Version of the script
SCRIPT_VERSION = "1.0.0"

# API base URL
BASE_URL = "https://apollo.jfit.co"
LOGIN_ENDPOINT = "exerciser/login"
WORKOUTS_ENDPOINT = "exerciser/{exerciser_id}/workouts"

app = Flask(__name__)

# Function to log in using XID
def login(USERNAME, PASSWORD, API_KEY, DEBUG=False):
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

    if DEBUG:
        print(f"Debug: Sending POST request to {url}")
        print(f"Debug: Headers: {headers}")
        print(f"Debug: Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(url, json=payload, headers=headers)

    if DEBUG:
        print(f"Debug: Status Code: {response.status_code}")
        print(f"Debug: Response Text: {response.text}")

    if response.status_code == 200:
        data = response.json()
        return data.get("token"), data.get("id")
    else:
        print(f"Login failed: {response.status_code}")
        return None, None

# Function to fetch workout data from API
def fetch_workouts(token, exerciser_id, API_KEY, DEBUG=False):
    endpoint = WORKOUTS_ENDPOINT.format(exerciser_id=exerciser_id)
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": API_KEY
    }

    if DEBUG:
        print(f"Debug: Sending GET request to {url}")
        print(f"Debug: Headers: {headers}")

    response = requests.get(url, headers=headers)

    if DEBUG:
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
    global USERNAME, PASSWORD, API_KEY, DEBUG

    if not USERNAME or not PASSWORD or not API_KEY:
        return jsonify({"error": "Missing credentials"}), 500

    # Log in to the external API
    token, exerciser_id = login(USERNAME, PASSWORD, API_KEY, DEBUG)

    if token and exerciser_id:
        workouts = fetch_workouts(token, exerciser_id, API_KEY, DEBUG)
        if workouts:
            return jsonify({"workouts": workouts}), 200
        else:
            return jsonify({"error": "No workouts found"}), 404
    else:
        return jsonify({"error": "Login failed"}), 500

if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Workout Data Server')
    parser.add_argument('--USERNAME', required=True, help='Username for login')
    parser.add_argument('--PASSWORD', required=True, help='Password for login')
    parser.add_argument('--API_KEY', required=True, help='API Key')
    parser.add_argument('--DEBUG', required=False, default='false', help='Enable debug mode (true/false)')
    args = parser.parse_args()

    # Convert the DEBUG argument to a boolean
    DEBUG = args.DEBUG.lower() == 'true'

    # Set the variables globally so they can be accessed in the Flask route
    USERNAME = args.USERNAME
    PASSWORD = args.PASSWORD
    API_KEY = args.API_KEY

    # Print startup information
    print(f"Starting server - Version: {SCRIPT_VERSION}")
    print(f"USERNAME: {USERNAME}")
    print(f"PASSWORD: {'*' * len(PASSWORD)}")  # Mask password
    print(f"API_KEY: {'*' * len(API_KEY)}")    # Mask API key
    print(f"DEBUG: {DEBUG}")

    # Run the server
    app.run(host='0.0.0.0', port=5000, debug=DEBUG)
