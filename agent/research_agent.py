from .base_agent import BaseAgent
from typing import Dict, Any
from langchain.schema import HumanMessage, SystemMessage
from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool
import os

class ResearchAgent(BaseAgent):
    """Agent specialized in destination research and attractions"""
    
    def __init__(self, model_provider: str = "groq"):
        super().__init__(
            name="Research Agent",
            role="Destination research and attraction discovery specialist",
            model_provider=model_provider
        )
        self.google_places_search = GooglePlaceSearchTool(os.getenv("GPLACES_API_KEY"))
        self.tavily_search = TavilyPlaceSearchTool()
        
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process research tasks"""
        task_type = task.get("type", "destination_research")
        
        if task_type == "destination_research":
            return await self._research_destination(task)
        elif task_type == "attractions":
            return await self._find_attractions(task)
        else:
            return await self._general_research(task)
            
    async def _research_destination(self, task: Dict) -> Dict:
        """Research destination details"""
        destination = task.get("destination")
        duration = task.get("duration", "5 days")
        
        system_prompt = f"""You are a destination research specialist. Research {destination} for a {duration} trip.
        
        Focus on:
        1. Key highlights and must-visit places
        2. Best time to visit
        3. Local customs and culture
        4. Safety considerations
        5. Unique experiences
        
        Provide comprehensive but concise information."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Research {destination} for a {duration} trip")
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # Get attractions data properly
        try:
            attractions = self.google_places_search.google_search_attractions(destination)
        except:
            attractions = self.tavily_search.tavily_search_attractions(destination)
        
        # Store in memory
        self.add_to_memory({
            "task": "destination_research",
            "destination": destination,
            "response": response.content
        })
        
        return {
            "agent": self.name,
            "task_type": "destination_research",
            "destination": destination,
            "research_data": response.content,
            "attractions": attractions,
            "status": "completed"
        }
        
    async def _find_attractions(self, task: Dict) -> Dict:
        """Find attractions"""
        destination = task.get("destination")
        
        try:
            attractions = self.google_places_search.google_search_attractions(destination)
            restaurants = self.google_places_search.google_search_restaurants(destination)
            activities = self.google_places_search.google_search_activity(destination)
        except:
            attractions = self.tavily_search.tavily_search_attractions(destination)
            restaurants = self.tavily_search.tavily_search_restaurants(destination)
            activities = self.tavily_search.tavily_search_activity(destination)
            
        return {
            "agent": self.name,
            "task_type": "attractions",
            "destination": destination,
            "attractions": attractions,
            "restaurants": restaurants,
            "activities": activities,
            "status": "completed"
        }
        
    async def _general_research(self, task: Dict) -> Dict:
        """General research fallback"""
        query = task.get("query", "")
        
        messages = [
            SystemMessage(content="You are a travel research specialist."),
            HumanMessage(content=query)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        return {
            "agent": self.name,
            "task_type": "general_research",
            "response": response.content,
            "status": "completed"
        }