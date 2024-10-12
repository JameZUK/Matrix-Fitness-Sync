from flask import Flask, jsonify, request
import requests
import json
import argparse
import datetime

# Version of the script
SCRIPT_VERSION = "1.0.0"

# API base URL
BASE_URL = "https://apollo.jfit.co"
LOGIN_ENDPOINT = "exerciser/login"
WORKOUTS_ENDPOINT = "exerciser/{exerciser_id}/workouts"

app = Flask(__name__)

# Log incoming requests for debugging
@app.before_request
def log_request_info():
    if DEBUG:
        print(f"Debug: Incoming request: {request.method} {request.path}")
        print(f"Debug: Request headers: {request.headers}")
        print(f"Debug: Request body: {request.get_data()}")

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
        print(f"Debug: Attempting to log in. POST request to {url}")
        print(f"Debug: Headers: {headers}")
        print(f"Debug: Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"Error: Failed to send POST request to {url}. Exception: {str(e)}")
        return None, None

    if DEBUG:
        print(f"Debug: Login response status code: {response.status_code}")

    if response.status_code == 200:
        try:
            data = response.json()
            token = data.get("token")
            exerciser_id = data.get("id")
            if DEBUG:
                print(f"Debug: Successfully logged in. Token: {token}, Exerciser ID: {exerciser_id}")
            return token, exerciser_id
        except Exception as e:
            print(f"Error: Failed to parse login response. Exception: {str(e)}")
            return None, None
    else:
        print(f"Error: Login failed with status code {response.status_code}. Response: {response.text}")
        return None, None

# Function to fetch workouts from the last 7 days
def fetch_workouts(token, exerciser_id, API_KEY, DEBUG=False):
    endpoint = WORKOUTS_ENDPOINT.format(exerciser_id=exerciser_id)
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "x-api-key": API_KEY
    }

    if DEBUG:
        print(f"Debug: Fetching workouts. GET request to {url}")
        print(f"Debug: Headers: {headers}")

    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        print(f"Error: Failed to send GET request to {url}. Exception: {str(e)}")
        return []

    if DEBUG:
        print(f"Debug: Fetch workouts response status code: {response.status_code}")

    if response.status_code == 200:
        try:
            full_workouts = response.json().get("workouts", [])
            if DEBUG:
                print(f"Debug: Total workouts fetched: {len(full_workouts)}")

            # Filter workouts from the last 7 days
            seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            filtered_workouts = []
            for workout in full_workouts:
                workout_time_str = workout.get("workout_time")
                if workout_time_str:
                    try:
                        # Parse the workout_time string into a datetime object
                        workout_time = datetime.datetime.strptime(workout_time_str, "%Y-%m-%dT%H:%M:%S.%fZ")
                        if workout_time >= seven_days_ago:
                            filtered_workouts.append(workout)
                    except Exception as e:
                        print(f"Error: Failed to parse workout_time '{workout_time_str}'. Exception: {str(e)}")
                        continue
            if DEBUG:
                print(f"Debug: Workouts from the last 7 days: {len(filtered_workouts)}")

            # Trim unnecessary fields
            trimmed_workouts = []
            for workout in filtered_workouts:
                trimmed_workout = {
                    "workout_id": workout.get("workout_id"),
                    "duration": workout.get("duration"),
                    "distance": workout.get("distance"),
                    "calories": workout.get("calories"),
                    "average_heart_rate": workout.get("average_heart_rate"),
                    "max_heart_rate": workout.get("max_heart_rate"),
                    "min_heart_rate": workout.get("min_heart_rate"),
                    "workout_time": workout.get("workout_time"),
                    "workout_type": workout.get("workout_type"),
                    "exercise_title": workout.get("exercise_title"),
                }
                trimmed_workouts.append(trimmed_workout)

            return trimmed_workouts
        except Exception as e:
            print(f"Error: Failed to process workouts. Exception: {str(e)}")
            return []
    else:
        print(f"Error: Failed to fetch workouts with status code {response.status_code}. Response: {response.text}")
        return []

# API endpoint to serve workout data to Home Assistant
@app.route('/api/workouts', methods=['GET'])
def workout_data():
    global USERNAME, PASSWORD, API_KEY, DEBUG

    if DEBUG:
        print("Debug: Starting /api/workouts endpoint")

    if not USERNAME or not PASSWORD or not API_KEY:
        print("Error: Missing credentials (USERNAME, PASSWORD, API_KEY)")
        return jsonify({"error": "Missing credentials"}), 500

    # Log in to the external API
    token, exerciser_id = login(USERNAME, PASSWORD, API_KEY, DEBUG)

    if not token or not exerciser_id:
        print("Error: Login failed. Could not retrieve token or exerciser_id.")
        return jsonify({"error": "Login failed"}), 500

    if DEBUG:
        print(f"Debug: Successfully logged in. Token: {token}, Exerciser ID: {exerciser_id}")

    # Fetch workouts from the last 7 days
    workouts = fetch_workouts(token, exerciser_id, API_KEY, DEBUG)

    if not workouts:
        print("Error: No workouts found in the last 7 days.")
        return jsonify({"error": "No workouts found"}), 404

    if DEBUG:
        print(f"Debug: Returning {len(workouts)} workouts from the last 7 days.")

    return jsonify({"workouts": workouts}), 200

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
