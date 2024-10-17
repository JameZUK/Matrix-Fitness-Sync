from flask import Flask, jsonify, request
import requests
import json
import argparse
import datetime
from waitress import serve  # Import Waitress
import threading
import time

# Version of the script
SCRIPT_VERSION = "1.1.0"

# API base URL
BASE_URL = "https://apollo.jfit.co"
LOGIN_ENDPOINT = "exerciser/login"
WORKOUTS_ENDPOINT = "exerciser/{exerciser_id}/workouts"

app = Flask(__name__)

# Global variables
USERNAME = ""
PASSWORD = ""
API_KEY = ""
DEBUG = False
POLL_SECONDS = 60  # Default polling interval

# Cache for workouts
cache = {
    "workouts": [],
    "last_updated": None,
    "error": None
}
cache_lock = threading.Lock()

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

            # Sort workouts by 'workout_time' in descending order (most recent first)
            full_workouts.sort(key=lambda x: x.get('workout_time', ''), reverse=True)

            return full_workouts
        except Exception as e:
            print(f"Error: Failed to process workouts. Exception: {str(e)}")
            return []
    else:
        print(f"Error: Failed to fetch workouts with status code {response.status_code}. Response: {response.text}")
        return []

def poll_external_api():
    global cache
    while True:
        if DEBUG:
            print(f"Debug: Starting polling cycle at {datetime.datetime.now()}")

        token, exerciser_id = login(USERNAME, PASSWORD, API_KEY, DEBUG)

        if token and exerciser_id:
            workouts = fetch_workouts(token, exerciser_id, API_KEY, DEBUG)
            with cache_lock:
                if workouts:
                    cache["workouts"] = workouts
                    cache["last_updated"] = datetime.datetime.utcnow().isoformat() + "Z"
                    cache["error"] = None
                    if DEBUG:
                        print(f"Debug: Cache updated with {len(workouts)} workouts.")
                else:
                    cache["error"] = "No workouts fetched."
                    if DEBUG:
                        print("Debug: No workouts fetched during this cycle.")
        else:
            with cache_lock:
                cache["error"] = "Failed to log in."
                if DEBUG:
                    print("Debug: Failed to log in during this polling cycle.")

        if DEBUG:
            print(f"Debug: Polling cycle completed. Sleeping for {POLL_SECONDS} seconds.")

        time.sleep(POLL_SECONDS)

@app.route('/api/workout', methods=['GET'])
def get_workout():
    global cache

    if DEBUG:
        print("Debug: Starting /api/workout endpoint")

    # Get 'n' parameter from query string (default to 1 if not provided)
    try:
        n = int(request.args.get('n', 1))
    except ValueError:
        return jsonify({"error": "Parameter 'n' must be an integer"}), 400

    if n < 1:
        return jsonify({"error": "Parameter 'n' must be a positive integer"}), 400

    if DEBUG:
        print(f"Debug: Parameter 'n' received: {n}")

    with cache_lock:
        if cache["error"]:
            return jsonify({"error": cache["error"]}), 500

        workouts = cache["workouts"]

    if not workouts:
        return jsonify({"error": "No workouts available. Please wait for the first polling cycle."}), 503

    # Ensure 'n' is within the range of available workouts
    if n > len(workouts):
        return jsonify({"error": f"Parameter 'n' is out of range. Only {len(workouts)} workouts available."}), 400

    # Get the nth previous workout (1-based indexing)
    workout = workouts[n - 1]

    if DEBUG:
        print(f"Debug: Returning workout #{n}")

    # Trim unnecessary fields if needed
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
        # Include other fields if necessary
    }

    return jsonify({"workout": trimmed_workout}), 200

def start_polling_thread():
    polling_thread = threading.Thread(target=poll_external_api, daemon=True)
    polling_thread.start()
    if DEBUG:
        print("Debug: Polling thread started.")

if __name__ == '__main__':
    import sys

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Workout Data Server')
    parser.add_argument('--USERNAME', required=True, help='Username for login')
    parser.add_argument('--PASSWORD', required=True, help='Password for login')
    parser.add_argument('--API_KEY', required=True, help='API Key')
    parser.add_argument('--DEBUG', required=False, default='false', help='Enable debug mode (true/false)')
    parser.add_argument('--poll_seconds', required=False, type=int, default=60, help='Polling interval in seconds')
    args = parser.parse_args()

    # Convert the DEBUG argument to a boolean
    DEBUG = args.DEBUG.lower() == 'true'

    # Set the polling interval
    POLL_SECONDS = args.poll_seconds
    if POLL_SECONDS < 5:
        print("Warning: Polling interval too low. Setting to minimum of 5 seconds.")
        POLL_SECONDS = 5

    # Set the variables globally so they can be accessed in the polling thread and Flask route
    USERNAME = args.USERNAME
    PASSWORD = args.PASSWORD
    API_KEY = args.API_KEY

    # Print startup information
    print(f"Starting server - Version: {SCRIPT_VERSION}")
    print(f"USERNAME: {USERNAME}")
    print(f"PASSWORD: {'*' * len(PASSWORD)}")  # Mask password
    print(f"API_KEY: {'*' * len(API_KEY)}")    # Mask API key
    print(f"DEBUG: {DEBUG}")
    print(f"POLL_SECONDS: {POLL_SECONDS}")

    # Start the background polling thread
    start_polling_thread()

    # Run the server using Waitress
    try:
        serve(app, host='0.0.0.0', port=5000, threads=4, url_scheme='http')
    except KeyboardInterrupt:
        print("Shutting down server...")
        sys.exit(0)
