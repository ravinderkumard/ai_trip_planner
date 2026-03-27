from utils.place_info_search import TavilyPlaceSearchTool
from utils.prompt_injection_guard import validate_place_query
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv

class PlaceSearchTool:
    def __init__(self, tracer=None):
        load_dotenv()
        self.tracer = tracer
        self.tavily_search = TavilyPlaceSearchTool()
        self.place_search_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the place search tool"""
        @tool
        def search_attractions(place:str) -> str:
            """Search attractions of a place"""
            place = validate_place_query(place)
            if self.tracer:
                self.tracer.log("tool_start", "Running search_attractions", tool="search_attractions", place=place)
            attraction_result = self.tavily_search.tavily_search_attractions(place)
            if self.tracer:
                self.tracer.log("tool_end", "Finished search_attractions", tool="search_attractions", place=place)
            return f"Following are the attractions of {place}: {attraction_result}"
        
        @tool
        def search_restaurants(place:str) -> str:
            """Search restaurants of a place"""
            place = validate_place_query(place)
            if self.tracer:
                self.tracer.log("tool_start", "Running search_restaurants", tool="search_restaurants", place=place)
            restaurants_result = self.tavily_search.tavily_search_restaurants(place)
            if self.tracer:
                self.tracer.log("tool_end", "Finished search_restaurants", tool="search_restaurants", place=place)
            return f"Following are the restaurants of {place}: {restaurants_result}"
        
        @tool
        def search_activities(place:str) -> str:
            """Search activities of a place"""
            place = validate_place_query(place)
            if self.tracer:
                self.tracer.log("tool_start", "Running search_activities", tool="search_activities", place=place)
            activities_result = self.tavily_search.tavily_search_activity(place)
            if self.tracer:
                self.tracer.log("tool_end", "Finished search_activities", tool="search_activities", place=place)
            return f"Following are the activities of {place}: {activities_result}"
        
        @tool
        def search_transportation(place:str) -> str:
            """Search transportation of a place"""
            place = validate_place_query(place)
            if self.tracer:
                self.tracer.log("tool_start", "Running search_transportation", tool="search_transportation", place=place)
            transportation_result = self.tavily_search.tavily_search_transportation(place)
            if self.tracer:
                self.tracer.log("tool_end", "Finished search_transportation", tool="search_transportation", place=place)
            return f"Following are the modes of transportation available in {place}: {transportation_result}"
        
        return [search_attractions, search_restaurants, search_activities, search_transportation]
