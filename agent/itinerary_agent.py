from .base_agent import BaseAgent
from typing import Dict, Any
from langchain.schema import HumanMessage, SystemMessage

class ItineraryAgent(BaseAgent):
    """Agent specialized in creating detailed day-by-day itineraries"""
    
    def __init__(self, model_provider: str = "groq"):
        super().__init__(
            name="Itinerary Agent",
            role="Day-by-day itinerary planning and scheduling specialist",
            model_provider=model_provider
        )
        
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process itinerary planning tasks"""
        task_type = task.get("type", "create_itinerary")
        
        if task_type == "optimize_schedule":
            return await self._optimize_schedule(task)
        else:
            return await self._create_detailed_itinerary(task)
            
    async def _create_detailed_itinerary(self, task: Dict) -> Dict:
        """Create detailed day-by-day itinerary"""
        destination = task.get("destination")
        duration = task.get("duration", 5)
        attractions = task.get("attractions", "")
        weather_info = task.get("weather_info", "")
        budget_info = task.get("budget_info", "")
        preferences = task.get("preferences", "")
        
        system_prompt = f"""You are an expert itinerary planner. Create a detailed {duration}-day itinerary for {destination}.
        
        Available Information:
        - Attractions: {attractions}
        - Weather: {weather_info}
        - Budget: {budget_info}
        - Preferences: {preferences}
        
        For each day, provide:
        1. **Day X: [Theme/Focus]**
        2. **Morning (9:00 AM - 12:00 PM):**
           - Activity with location
           - Estimated cost
           - Duration
        3. **Afternoon (12:00 PM - 6:00 PM):**
           - Lunch recommendation
           - Main activities
           - Transportation details
        4. **Evening (6:00 PM - 10:00 PM):**
           - Dinner recommendations
           - Evening activities
        5. **Daily Tips:** Weather considerations, packing, local customs
        6. **Estimated Daily Cost:** Breakdown of expenses
        
        Make it practical, enjoyable, and well-paced. Consider travel time between locations.
        Include both popular tourist spots and local hidden gems."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create comprehensive {duration}-day itinerary for {destination}")
        ]
        
        itinerary = await self.llm.ainvoke(messages)
        
        return {
            "agent": self.name,
            "task_type": "detailed_itinerary",
            "destination": destination,
            "duration": duration,
            "itinerary": itinerary.content,
            "status": "completed"
        }
        
    async def _optimize_schedule(self, task: Dict) -> Dict:
        """Optimize existing itinerary for better flow"""
        current_itinerary = task.get("itinerary")
        optimization_focus = task.get("focus", "time_efficiency")
        
        system_prompt = f"""You are an itinerary optimization specialist. Review and optimize this itinerary focusing on: {optimization_focus}
        
        Current Itinerary: {current_itinerary}
        
        Provide:
        1. Optimized schedule with improvements
        2. Explanation of changes made
        3. Benefits of the optimization
        4. Alternative options if applicable
        
        Focus areas:
        - Time efficiency: Minimize travel time between locations
        - Cost optimization: Reduce overall expenses
        - Experience quality: Enhance travel experiences
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Optimize this itinerary: {current_itinerary}")
        ]
        
        optimized = await self.llm.ainvoke(messages)
        
        return {
            "agent": self.name,
            "task_type": "schedule_optimization",
            "optimized_itinerary": optimized.content,
            "optimization_focus": optimization_focus,
            "status": "completed"
        }