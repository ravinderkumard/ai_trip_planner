from utils.expense_calculator import Calculator
from typing import List
from langchain.tools import tool

class CalculatorTool:
    def __init__(self, tracer=None):
        self.tracer = tracer
        self.calculator = Calculator()
        self.calculator_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the calculator tool"""
        @tool
        def estimate_total_hotel_cost(price_per_night:str, total_days:float) -> float:
            """Calculate total hotel cost"""
            if self.tracer:
                self.tracer.log("tool_start", "Running estimate_total_hotel_cost", tool="estimate_total_hotel_cost")
            result = self.calculator.multiply(price_per_night, total_days)
            if self.tracer:
                self.tracer.log("tool_end", "Finished estimate_total_hotel_cost", tool="estimate_total_hotel_cost", result=result)
            return result
        
        @tool
        def calculate_total_expense(*costs: float) -> float:
            """Calculate total expense of the trip"""
            if self.tracer:
                self.tracer.log("tool_start", "Running calculate_total_expense", tool="calculate_total_expense")
            result = self.calculator.calculate_total(*costs)
            if self.tracer:
                self.tracer.log("tool_end", "Finished calculate_total_expense", tool="calculate_total_expense", result=result)
            return result
        
        @tool
        def calculate_daily_expense_budget(total_cost: float, days: int) -> float:
            """Calculate daily expense"""
            if self.tracer:
                self.tracer.log("tool_start", "Running calculate_daily_expense_budget", tool="calculate_daily_expense_budget")
            result = self.calculator.calculate_daily_budget(total_cost, days)
            if self.tracer:
                self.tracer.log("tool_end", "Finished calculate_daily_expense_budget", tool="calculate_daily_expense_budget", result=result)
            return result
        
        return [estimate_total_hotel_cost, calculate_total_expense, calculate_daily_expense_budget]
