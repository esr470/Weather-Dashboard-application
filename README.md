# 🌦️ Weather Dashboard

A desktop weather application built with Python that displays current weather information and a 5-day forecast for a selected city.

## ✨ Features

- 🔍 Search for a city by name.
- 🌡️ Display current temperature and feels-like temperature.
- 💧 Show humidity and wind speed.
- 📅 View a 5-day weather forecast.
- 📊 Display forecast temperatures in a chart.
- 🕘 Save recently searched cities.

## 🛠️ Technologies Used

- Python
- Tkinter
- Open-Meteo API
- JSON
- urllib

## ⚙️ How It Works

1. The user enters a city name.
2. The application uses the Open-Meteo Geocoding API to find the city's coordinates.
3. It sends the coordinates to the Open-Meteo Forecast API.
4. The returned weather data is processed and displayed in the desktop interface.

## 🚀 How to Run

1. Install Python 3.
2. Clone or download this repository.
3. Open a terminal in the project folder.
4. Run the application:

```bash
python weather_dashboard.py
```

Replace `weather_dashboard.py` with the actual Python filename if it is different.

## 🌐 Weather Data Source

Weather data is retrieved from [Open-Meteo](https://open-meteo.com/).

## 📌 Note

Weather forecasts are estimates and may differ from actual weather conditions.

## 👩‍💻 Author

Esraa Ibrahim
