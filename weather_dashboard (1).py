"""
Weather Dashboard
------------------
A simple desktop app that shows the current weather and a 5-day
forecast for any city the user types in.

I used the Open-Meteo API because it's free and does not need an
API key or account (https://open-meteo.com).

How it works:
1. The user types a city name and presses Search.
2. We call the "geocoding" API first to turn the city name into
   latitude/longitude (since the weather API needs coordinates).
3. We call the "forecast" API with those coordinates to get the
   current weather + the next few days.
4. We show everything in the window, plus a small chart I draw by
   hand on a Canvas (no extra chart library needed).
5. The last few cities the user searched are saved in a text file
   so they show up as quick buttons next time.
"""

import tkinter as tk
import urllib.request
import urllib.parse
import json
import os
import datetime

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORY_FILE = "recent_cities.txt"

# Open-Meteo gives back a "weather code" number instead of a text
# description, so this dictionary translates the codes I actually
# care about into something readable + a little icon.
WEATHER_CODES = {
    0: ("Clear sky", "☀"),
    1: ("Mainly clear", "🌤"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁"),
    45: ("Fog", "🌫"),
    48: ("Fog", "🌫"),
    51: ("Light drizzle", "🌦"),
    53: ("Drizzle", "🌦"),
    55: ("Dense drizzle", "🌦"),
    61: ("Slight rain", "🌧"),
    63: ("Rain", "🌧"),
    65: ("Heavy rain", "🌧"),
    71: ("Slight snow", "❄"),
    73: ("Snow", "❄"),
    75: ("Heavy snow", "❄"),
    80: ("Rain showers", "🌦"),
    81: ("Rain showers", "🌦"),
    82: ("Violent showers", "🌧"),
    95: ("Thunderstorm", "⛈"),
    96: ("Thunderstorm", "⛈"),
    99: ("Thunderstorm", "⛈"),
}


def code_to_text(code):
    # fall back to something generic if the code is not in my table
    return WEATHER_CODES.get(code, ("Unknown", "?"))


# ---------------------------------------------------------------
# Functions that talk to the internet (API calls)
# ---------------------------------------------------------------

def call_api(url, params):
    """Small helper so I don't repeat the same urllib code twice."""
    full_url = url + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
    response = urllib.request.urlopen(request, timeout=8)
    text = response.read().decode("utf-8")
    return json.loads(text)


def find_city(city_name):
    """Turns a city name like 'Alexandria' into latitude/longitude.
    Returns None if the city was not found."""
    data = call_api(GEOCODE_URL, {"name": city_name, "count": 1})
    results = data.get("results")
    if not results:
        return None
    first = results[0]
    return {
        "name": first["name"],
        "country": first.get("country", ""),
        "lat": first["latitude"],
        "lon": first["longitude"],
    }


def get_weather(lat, lon):
    """Gets the current weather + next 6 days for a location."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 6,
    }
    return call_api(FORECAST_URL, params)


# ---------------------------------------------------------------
# Functions that just process data (no internet needed here,
# so these are the easiest ones to test on their own)
# ---------------------------------------------------------------

def get_current_info(weather_json):
    """Pulls out the 'right now' weather info we want to display."""
    c = weather_json["current"]
    text, icon = code_to_text(c["weather_code"])
    return {
        "temp": round(c["temperature_2m"]),
        "feels_like": round(c["apparent_temperature"]),
        "humidity": round(c["relative_humidity_2m"]),
        "wind": round(c["wind_speed_10m"]),
        "text": text,
        "icon": icon,
    }


def get_forecast_days(weather_json):
    """Builds a list of the next 5 days (skips today since 'current'
    already shows today)."""
    daily = weather_json["daily"]
    days = []
    for i in range(1, len(daily["time"])):
        text, icon = code_to_text(daily["weather_code"][i])
        days.append({
            "date": daily["time"][i],
            "max": round(daily["temperature_2m_max"][i]),
            "min": round(daily["temperature_2m_min"][i]),
            "text": text,
            "icon": icon,
        })
    return days


def weekday_name(date_text):
    # date_text looks like "2026-10-12", turn it into "Mon"
    day = datetime.date.fromisoformat(date_text)
    return day.strftime("%a")


# ---------------------------------------------------------------
# Saving the last few cities searched to a simple text file
# ---------------------------------------------------------------

def read_recent_cities():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    return [line for line in lines if line != ""]


def add_recent_city(city_text):
    cities = read_recent_cities()
    # remove it if it's already in the list, so it doesn't repeat
    if city_text in cities:
        cities.remove(city_text)
    cities.insert(0, city_text)
    cities = cities[:5]  # keep only the last 5
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for c in cities:
            f.write(c + "\n")


# ---------------------------------------------------------------
# The GUI (the actual window the user sees)
# ---------------------------------------------------------------

BG_COLOR = "#0B1220"
CARD_COLOR = "#121B2E"
CARD_COLOR_2 = "#1A2740"
BLUE = "#5EC8F8"
WHITE = "#F1F5F9"
GREY = "#8EA0B8"
RED = "#EF4444"


class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("820x600")
        self.root.configure(bg=BG_COLOR)

        # ---- top bar: title + search box ----
        title_label = tk.Label(root, text="🌤 Weather Dashboard", bg=BG_COLOR, fg=WHITE,
                               font=("Segoe UI", 20, "bold"))
        title_label.pack(anchor="w", padx=24, pady=(20, 10))

        search_frame = tk.Frame(root, bg=BG_COLOR)
        search_frame.pack(fill="x", padx=24)

        self.city_input = tk.Entry(search_frame, font=("Segoe UI", 12), width=30)
        self.city_input.pack(side="left", ipady=4)
        self.city_input.insert(0, "Alexandria")
        self.city_input.bind("<Return>", lambda event: self.on_search())

        search_button = tk.Button(search_frame, text="Search", command=self.on_search,
                                  bg=BLUE, fg="#0B1220", font=("Segoe UI", 11, "bold"),
                                  relief="flat", padx=16, pady=5, cursor="hand2")
        search_button.pack(side="left", padx=8)

        # ---- row of recent cities (filled in later) ----
        self.recent_frame = tk.Frame(root, bg=BG_COLOR)
        self.recent_frame.pack(fill="x", padx=24, pady=(8, 0))

        # ---- status / error message ----
        self.status_label = tk.Label(root, text="", bg=BG_COLOR, fg=GREY, font=("Segoe UI", 10))
        self.status_label.pack(fill="x", padx=24, pady=(6, 0))

        # ---- the area where weather info goes ----
        self.content_frame = tk.Frame(root, bg=BG_COLOR)
        self.content_frame.pack(fill="both", expand=True, padx=24, pady=10)

        self.show_recent_buttons()

    def show_recent_buttons(self):
        # clear old buttons first
        for widget in self.recent_frame.winfo_children():
            widget.destroy()

        cities = read_recent_cities()
        if not cities:
            return

        tk.Label(self.recent_frame, text="Recent:", bg=BG_COLOR, fg=GREY,
                 font=("Segoe UI", 9)).pack(side="left", padx=(0, 6))
        for city in cities:
            btn = tk.Button(self.recent_frame, text=city, bg=CARD_COLOR_2, fg=WHITE,
                            font=("Segoe UI", 9), relief="flat", padx=10, pady=3,
                            cursor="hand2",
                            command=lambda c=city: self.search_for(c))
            btn.pack(side="left", padx=3)

    def search_for(self, city_text):
        self.city_input.delete(0, tk.END)
        self.city_input.insert(0, city_text)
        self.on_search()

    def on_search(self):
        city_text = self.city_input.get().strip()
        if city_text == "":
            return

        self.status_label.config(text="Searching...", fg=GREY)
        self.root.update()  # refresh the window so "Searching..." shows right away

        try:
            place = find_city(city_text)
            if place is None:
                self.status_label.config(text=f'No city found called "{city_text}".', fg=RED)
                return

            weather_json = get_weather(place["lat"], place["lon"])
            current = get_current_info(weather_json)
            forecast_days = get_forecast_days(weather_json)

            label = place["name"]
            if place["country"]:
                label += ", " + place["country"]

            add_recent_city(label)
            self.show_recent_buttons()
            self.status_label.config(text="Showing weather for " + label, fg=GREY)
            self.draw_weather(current, forecast_days)

        except Exception as error:
            # anything can go wrong here (no internet, timeout, etc.)
            self.status_label.config(text="Something went wrong, check your internet connection.", fg=RED)
            print("Error:", error)  # helpful when testing in the terminal

    def draw_weather(self, current, days):
        # clear whatever was shown before
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # ---- current weather card ----
        card = tk.Frame(self.content_frame, bg=CARD_COLOR, padx=25, pady=20)
        card.pack(fill="x")

        left_side = tk.Frame(card, bg=CARD_COLOR)
        left_side.pack(side="left")
        tk.Label(left_side, text=current["icon"], bg=CARD_COLOR, fg=WHITE,
                 font=("Segoe UI", 42)).pack(side="left", padx=(0, 15))

        info_box = tk.Frame(left_side, bg=CARD_COLOR)
        info_box.pack(side="left")
        tk.Label(info_box, text=f'{current["temp"]}°C', bg=CARD_COLOR, fg=WHITE,
                 font=("Segoe UI", 30, "bold")).pack(anchor="w")
        tk.Label(info_box, text=current["text"], bg=CARD_COLOR, fg=BLUE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")

        right_side = tk.Frame(card, bg=CARD_COLOR)
        right_side.pack(side="right")
        details = [
            ("Feels like", f'{current["feels_like"]}°C'),
            ("Humidity", f'{current["humidity"]}%'),
            ("Wind", f'{current["wind"]} km/h'),
        ]
        for label_text, value_text in details:
            row = tk.Frame(right_side, bg=CARD_COLOR)
            row.pack(anchor="e", pady=2)
            tk.Label(row, text=label_text + ": ", bg=CARD_COLOR, fg=GREY,
                     font=("Segoe UI", 10)).pack(side="left")
            tk.Label(row, text=value_text, bg=CARD_COLOR, fg=WHITE,
                     font=("Segoe UI", 10, "bold")).pack(side="left")

        # ---- 5 day forecast cards ----
        tk.Label(self.content_frame, text="5-Day Forecast", bg=BG_COLOR, fg=WHITE,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(18, 8))

        days_row = tk.Frame(self.content_frame, bg=BG_COLOR)
        days_row.pack(fill="x")
        for day in days:
            day_box = tk.Frame(days_row, bg=CARD_COLOR_2, padx=12, pady=12)
            day_box.pack(side="left", padx=6)
            tk.Label(day_box, text=weekday_name(day["date"]), bg=CARD_COLOR_2, fg=GREY,
                     font=("Segoe UI", 10, "bold")).pack()
            tk.Label(day_box, text=day["icon"], bg=CARD_COLOR_2, fg=WHITE,
                     font=("Segoe UI", 22)).pack(pady=4)
            tk.Label(day_box, text=f'{day["max"]}° / {day["min"]}°', bg=CARD_COLOR_2, fg=WHITE,
                     font=("Segoe UI", 10)).pack()

        # ---- temperature chart (drawn by hand on a Canvas) ----
        tk.Label(self.content_frame, text="Temperature Trend", bg=BG_COLOR, fg=WHITE,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(18, 8))

        canvas = tk.Canvas(self.content_frame, width=772, height=150, bg=CARD_COLOR, highlightthickness=0)
        canvas.pack(fill="x")
        self.draw_chart(canvas, days)

    def draw_chart(self, canvas, days):
        if len(days) == 0:
            return

        left_margin = 40
        bottom_margin = 30
        width = 772
        height = 150
        plot_width = width - left_margin - 20
        plot_height = height - bottom_margin - 20

        all_temps = [d["max"] for d in days] + [d["min"] for d in days]
        lowest = min(all_temps)
        highest = max(all_temps)
        if highest == lowest:
            highest += 1  # avoid dividing by zero below
        temp_range = highest - lowest

        gap = plot_width / (len(days) - 1) if len(days) > 1 else 0

        def x_pos(i):
            return left_margin + i * gap

        def y_pos(temp):
            # higher temperature = higher on screen = smaller y value
            return 20 + plot_height - ((temp - lowest) / temp_range) * plot_height

        # draw the max-temperature line by connecting points one by one
        for i in range(len(days) - 1):
            x1, y1 = x_pos(i), y_pos(days[i]["max"])
            x2, y2 = x_pos(i + 1), y_pos(days[i + 1]["max"])
            canvas.create_line(x1, y1, x2, y2, fill=BLUE, width=2)

        # draw the min-temperature line too, in grey
        for i in range(len(days) - 1):
            x1, y1 = x_pos(i), y_pos(days[i]["min"])
            x2, y2 = x_pos(i + 1), y_pos(days[i + 1]["min"])
            canvas.create_line(x1, y1, x2, y2, fill=GREY, width=2)

        # dots + day labels + the max temperature number on top
        for i, day in enumerate(days):
            x = x_pos(i)
            y_max = y_pos(day["max"])
            y_min = y_pos(day["min"])
            canvas.create_oval(x - 3, y_max - 3, x + 3, y_max + 3, fill=BLUE, outline="")
            canvas.create_oval(x - 3, y_min - 3, x + 3, y_min + 3, fill=GREY, outline="")
            canvas.create_text(x, y_max - 12, text=f'{day["max"]}°', fill=BLUE, font=("Segoe UI", 8, "bold"))
            canvas.create_text(x, height - 10, text=weekday_name(day["date"]), fill=GREY, font=("Segoe UI", 8))


if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()
