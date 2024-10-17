
# Matrix-Fitness-Sync Home Assistant Add-on

Matrix-Fitness-Sync is a Home Assistant add-on designed to sync fitness data from Matrix fitness equipment (e.g., treadmills, bikes) to Home Assistant. The add-on collects workout data and exposes it through a REST API, allowing easy integration with Home Assistant sensors to monitor your workouts directly from the Home Assistant dashboard.

## Features

- Sync workout data from Matrix fitness equipment
- Exposes workout data via a REST API for easy integration
- Configurable polling interval for fetching workout data
- Provides detailed workout metrics like duration, distance, calories burned, and heart rate statistics
- Built-in caching to reduce redundant API calls
- Waitress-based web server for enhanced performance
- Logging with optional debug mode

## New Features in v1.1.1

- **Waitress Web Server**: The Flask app is now served using Waitress, improving performance and scalability.
- **Custom Polling Interval**: The polling interval is now configurable with a minimum of 120 seconds.
- **Improved Logging**: Enhanced logging system with DEBUG and INFO modes to capture more detailed events.
- **Global Cache Locking**: Thread-safe cache with locking ensures consistent and up-to-date workout data.

## Installation

To install Matrix-Fitness-Sync as a third-party Home Assistant add-on:

1. Navigate to your Home Assistant web interface.

2. Go to **Settings** > **Add-ons** > **Add-on Store**.

3. In the **Add-on Store**, click the three dots menu (in the top right corner) and select **Repositories**.

4. Add the following repository URL:
   ```
   https://github.com/JameZUK/Matrix-Fitness-Sync
   ```

5. Find `Matrix-Fitness-Sync` in the list of add-ons and click **Install**.

6. After installation, go to the add-on details page and click **Start** to run the add-on.

7. Optionally, enable **Start on boot** and **Watchdog** to ensure the add-on automatically starts with Home Assistant and restarts if it crashes.

## Configuration

The add-on exposes the following REST API endpoint:

- `/api/workout?n=1`: Returns the details of the latest workout (with `n` being the number of workouts to fetch).

### Example REST API Response

```json
{
  "workout": {
    "workout_id": "12345",
    "duration": 3600,
    "distance": 5000,
    "calories": 300,
    "average_heart_rate": 120,
    "max_heart_rate": 150,
    "min_heart_rate": 100,
    "workout_time": "2024-10-10T12:00:00Z",
    "workout_type": "Running",
    "exercise_title": "Treadmill Run"
  }
}
```

## Home Assistant Sensor Setup

To integrate the workout data into Home Assistant as sensors, you can use the following configuration in your `configuration.yaml` file.

### REST Sensor for Latest Workout

```yaml
sensor:
  - platform: rest
    name: "Latest Workout"
    resource: "http://<DOCKERNAME>:5000/api/workout?n=1"
    method: GET
    headers:
      Content-Type: application/json
    scan_interval: 120
    json_attributes_path: "$.workout"
    value_template: "{{ value_json.workout.workout_id }}"
    json_attributes:
      - duration
      - distance
      - calories
      - average_heart_rate
      - max_heart_rate
      - min_heart_rate
      - workout_time
      - workout_type
      - exercise_title
```

Replace `<DOCKERNAME>` with the actual Docker container name or IP address where the add-on is running.

### Template Sensors

You can define individual template sensors to extract specific attributes from the latest workout, with number rounding applied:

```yaml
sensor:
  - platform: template
    sensors:
      workout_duration:
        friendly_name: "Workout Duration"
        unit_of_measurement: "minutes"
        value_template: "{{ (state_attr('sensor.latest_workout', 'duration') | int / 60) | round(2) }}"
      workout_distance:
        friendly_name: "Workout Distance"
        unit_of_measurement: "km"
        value_template: "{{ (state_attr('sensor.latest_workout', 'distance') | float / 1000) | round(2) }}"
      workout_calories:
        friendly_name: "Workout Calories"
        unit_of_measurement: "kcal"
        value_template: "{{ state_attr('sensor.latest_workout', 'calories') | round(2) }}"
      workout_average_heart_rate:
        friendly_name: "Average Heart Rate"
        unit_of_measurement: "bpm"
        value_template: "{{ state_attr('sensor.latest_workout', 'average_heart_rate') | round(2) }}"
      workout_max_heart_rate:
        friendly_name: "Max Heart Rate"
        unit_of_measurement: "bpm"
        value_template: "{{ state_attr('sensor.latest_workout', 'max_heart_rate') | round(2) }}"
      workout_min_heart_rate:
        friendly_name: "Min Heart Rate"
        unit_of_measurement: "bpm"
        value_template: "{{ state_attr('sensor.latest_workout', 'min_heart_rate') | round(2) }}"
```

### Example Dashboard Card

Once you have added the sensors, you can display the data on your Home Assistant dashboard using a card:

```yaml
type: entities
title: Latest Workout Stats
entities:
  - entity: sensor.workout_duration
  - entity: sensor.workout_distance
  - entity: sensor.workout_calories
  - entity: sensor.workout_average_heart_rate
  - entity: sensor.workout_max_heart_rate
  - entity: sensor.workout_min_heart_rate
```

## API Endpoints

The following API endpoints are available for retrieving workout data:

- `/api/workout?n=1`: Fetches the latest workout. Adjust `n` to get multiple workouts (e.g., `/api/workout?n=5` for the last 5 workouts).

## Development

If you'd like to contribute or modify the add-on, follow these steps:

1. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/JameZUK/Matrix-Fitness-Sync.git
   ```

2. Navigate into the repository:
   ```bash
   cd Matrix-Fitness-Sync
   ```

3. Make any necessary changes to the source code.

4. Push your changes to your fork or submit a pull request to the original repository.

## Issues

If you encounter any issues or have suggestions for improvements, feel free to open an issue on GitHub.

## License

This project is licensed under the MIT License.
