from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import serial
import time

app = Flask(__name__)

API_KEY = '36330ab1222f487fb2260325240701'

# Define the serial port and baud rate
ser = serial.Serial('COM3', 9600, timeout=1)

def read_sensor_data(plant_name, water_level, will_it_rain):
    # Send the plant name, water level, and will_it_rain to Arduino
    ser.write(f'{plant_name},{water_level},{will_it_rain}\n'.encode())
    
    # Read and decode the response from Arduino
    time.sleep(1)  # Wait for the Arduino to respond
    response = ser.readline().decode().strip()
    return response

def get_weather(city, country, plant_name):
    current_url = "https://api.weatherapi.com/v1/current.json"
    future_url = "https://api.weatherapi.com/v1/forecast.json"
    params = {
        'q': f"{city},{country}",
        'key': API_KEY,
    }
    paramsw = {
        'q': f"{city},{country}",
        'key': API_KEY,
        'days': 1
    }

    try:
        response = requests.get(current_url, params=params)
        res = requests.get(future_url, params=paramsw)
        data = response.json()
        w = res.json()

        if response.status_code == 200:
            temperature = data.get('current', {}).get('temp_c')
            description = data.get('current', {}).get('condition', {}).get('text')
            humidity = data.get('current', {}).get('humidity')
            will_it_rain = w.get('forecast', {}).get('forecastday', [{}])[0].get('hour', [{}])[0].get('will_it_rain')

            # Read water level data for a specific plant from CSV using pandas
            water_level = get_water_level_from_csv(plant_name)

            # Read sensor data for a specific plant
            plant_data = read_sensor_data(plant_name, water_level, will_it_rain)

            if temperature is not None and description is not None:
                return {
                    'temperature': temperature,
                    'description': description,
                    'humidity': humidity,
                    'will_it_rain': will_it_rain,
                    'plant_data': plant_data
                }
            else:
                return {'error': 'Temperature or description not found in the API response'}
        else:
            return {'error': data.get('error', {}).get('message', 'Unknown error')}
    except Exception as e:
        return {'error': str(e)}

def get_water_level_from_csv(plant_name):
    # Read the CSV file using pandas
    df = pd.read_csv('plant-waterlevel.csv')

    # Filter the dataframe based on the plant name
    plant_data = df[df['Plant Name'] == plant_name]

    if not plant_data.empty:
        # Retrieve the water level for the specified plant
        water_level = plant_data.iloc[0]['Water Level Required']
        return water_level
    else:
        return None  # Return None if plant name is not found in the CSV

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_weather', methods=['GET'])
def api_get_weather():
    city = request.args.get('city')
    country = request.args.get('country')
    plant_name = request.args.get('plant_name')  # Extract plant_name from the request

    if city and country and plant_name:
        # Sending values to Arduino
        water_level_required = get_water_level_from_csv(plant_name)
        will_it_rain = 0  # You can update this based on your logic
        read_sensor_data(plant_name, water_level_required, will_it_rain)

        # Getting weather data
        weather_data = get_weather(city, country, plant_name)
        return jsonify(weather_data)
    else:
        return jsonify({'error': 'City, country, and plant_name are required'})

if __name__ == '__main__':
    app.run(debug=True)
    ser.close()  # Close the serial port when done
