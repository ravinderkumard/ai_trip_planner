import logging

import requests

logger = logging.getLogger(__name__)


class CurrencyConverter:
    def __init__(self, api_key: str):
        self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/"
        self.timeout = (5, 15)
    
    def convert(self, amount:float, from_currency:str, to_currency:str):
        """Convert the amount from one currency to another"""
        url = f"{self.base_url}/{from_currency}"
        try:
            response = requests.get(url, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.warning(
                "Currency conversion request failed for from=%s to=%s",
                from_currency,
                to_currency,
                exc_info=True,
            )
            raise RuntimeError("Currency conversion service is unavailable.") from exc
        if response.status_code != 200:
            logger.warning(
                "Currency conversion request returned status %s for from=%s to=%s",
                response.status_code,
                from_currency,
                to_currency,
            )
            raise RuntimeError("Currency conversion service returned an error.")
        rates = response.json()["conversion_rates"]
        if to_currency not in rates:
            logger.warning(
                "Target currency %s not found in conversion rates for source=%s",
                to_currency,
                from_currency,
            )
            raise ValueError(f"{to_currency} not found in exchange rates.")
        return amount * rates[to_currency]
