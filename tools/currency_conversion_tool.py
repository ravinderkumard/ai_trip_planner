import os
from utils.currency_converter import CurrencyConverter
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv

class CurrencyConverterTool:
    def __init__(self, tracer=None):
        load_dotenv()
        self.tracer = tracer
        self.api_key = os.environ.get("EXCHANGE_RATE_API_KEY")
        self.currency_service = CurrencyConverter(self.api_key)
        self.currency_converter_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the currency converter tool"""
        @tool
        def convert_currency(amount:float, from_currency:str, to_currency:str):
            """Convert amount from one currency to another"""
            if self.tracer:
                self.tracer.log("tool_start", "Running convert_currency", tool="convert_currency", amount=amount, from_currency=from_currency, to_currency=to_currency)
            result = self.currency_service.convert(amount, from_currency, to_currency)
            if self.tracer:
                self.tracer.log("tool_end", "Finished convert_currency", tool="convert_currency", result=result)
            return result
        
        return [convert_currency]
