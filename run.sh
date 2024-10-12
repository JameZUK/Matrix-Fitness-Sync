#!/usr/bin/with-contenv bashio
echo "Starting Flask server..."

# Load options from config
username=$(bashio::config 'username')
password=$(bashio::config 'password')
api_key=$(bashio::config 'api_key')
debug=$(bashio::config 'debug')

export username=$username
export password=$password
export api_key=$api_key
export debug=$debug
echo $username

# Run the Python script
while true
do
  python3 workout_data.py --USERNAME $username --PASSWORD $passwors --API_KEY $api_key --DEBUG $debug
  sleep 2
  echo "Restarting..."
done
