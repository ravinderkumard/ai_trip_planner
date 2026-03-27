import logging

import requests

logger = logging.getLogger(__name__)


class WeatherForecastTool:
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.timeout = (5, 15)

    def get_current_weather(self, place:str):
        """Get current weather of a place"""
        try:
            url = f"{self.base_url}/weather"
            params = {
                "q": place,
                "appid": self.api_key,
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "Current weather request failed with status %s for place=%s",
                response.status_code,
                place,
            )
            return {}
        except requests.RequestException:
            logger.warning("Current weather request failed for place=%s", place, exc_info=True)
            return {}
    
    def get_forecast_weather(self, place:str):
        """Get weather forecast of a place"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "q": place,
                "appid": self.api_key,
                "cnt": 10,
                "units": "metric"
            }
            response = requests.get(url, params=params, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            logger.warning(
                "Forecast weather request failed with status %s for place=%s",
                response.status_code,
                place,
            )
            return {}
        except requests.RequestException:
            logger.warning("Forecast weather request failed for place=%s", place, exc_info=True)
            return {}
