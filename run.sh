#!/usr/bin/with-contenv bashio
echo "Starting Flask server..."

# Load options from config
username=$(bashio::config 'username')
password=$(bashio::config 'password')
api_key=$(bashio::config 'api_key')
debug=$(bashio::config 'debug')

# Run the Python script
python3 workout_data.py "$username" "$password" "$api_key" "$debug"

