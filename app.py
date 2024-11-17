from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

API_KEY = '36330ab1222f487fb2260325240701'

def get_weather(city, country):
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
            if temperature is not None and description is not None:
                return {'temperature': temperature, 'description': description, 'humidity': humidity, 'will_it_rain': will_it_rain}
            else:
                return {'error': 'Temperature or description not found in the API response'}
        else:
            return {'error': data.get('error', {}).get('message', 'Unknown error')}
    except Exception as e:
        return {'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_weather', methods=['GET'])
def api_get_weather():
    city = request.args.get('city')
    country = request.args.get('country')
    if city and country:
        weather_data = get_weather(city, country)
        return jsonify(weather_data)
    else:
        return jsonify({'error': 'Both city and country are required'})

if __name__ == '__main__':
    app.run(debug=True)
