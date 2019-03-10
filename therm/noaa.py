from collections import namedtuple
from datetime import datetime, timedelta
from time import sleep
import json

from noaa_sdk import noaa
from display import display_weather

_NOAA_REFRESH = timedelta(hours=1)
_LAST_REFRESH = None

Summary = namedtuple('summary', ['name', 'temp', 'wind', 'description'])

line = {'number': 156, 'name': '', 'startTime': '2019-03-15T14:00:00-04:00', 'endTime': '2019-03-15T15:00:00-04:00',
        'isDaytime': True, 'temperature': 51, 'temperatureUnit': 'F', 'temperatureTrend': None, 'windSpeed': '14 mph',
        'windDirection': 'SW', 'icon': 'https://api.weather.gov/icons/land/day/rain?size=small',
        'shortForecast': 'Chance Light Rain', 'detailedForecast': ''}

n = noaa.NOAA()


def _shorten_wind(wind):
    """
    Args:
        wind (str): Wind description

    Returns:
        str: shortened description
    """
    return wind.replace(" to ", "-")

def _shorten_time_desciption(time_description):
    time_description = time_description.replace("This ", "")
    time_description = time_description.replace("Night", "Nt")
    time_description = time_description.replace("Tonight", "Night")
    return time_description


def _summarize(weather_json):
    name = _shorten_time_desciption(weather_json['name'])
    temp = weather_json['temperature']
    wind = _shorten_wind(weather_json['windSpeed'])
    forc = weather_json['shortForecast']
    return Summary(name, "{}°".format(temp), wind, forc)


def get_summary(zip='02141'):
    res = n.get_forecasts(zip, 'US', hourly=False)
    now = _summarize(res[0])
    soon = _summarize(res[1])
    return now, soon


while True:
    if not _LAST_REFRESH or datetime.utcnow() - _LAST_REFRESH > _NOAA_REFRESH:
        now, soon = get_summary()
        _LAST_REFRESH = datetime.utcnow()
        print(json.dumps(now._asdict(), indent=2))
        print(json.dumps(soon._asdict(), indent=2))
    display_weather(now, soon)
