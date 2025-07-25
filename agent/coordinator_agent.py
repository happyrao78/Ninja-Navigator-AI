from .base_agent import BaseAgent
from .research_agent import ResearchAgent
from .weather_agent import WeatherAgent
from .budget_agent import BudgetAgent
from .itinerary_agent import ItineraryAgent
from typing import Dict, Any
from langchain.schema import HumanMessage, SystemMessage
import asyncio
import re

class CoordinatorAgent(BaseAgent):
    """Main coordinator that orchestrates all specialized agents"""
    
    def __init__(self, model_provider: str = "groq"):
        super().__init__(
            name="Coordinator Agent",
            role="Travel planning orchestrator and agent coordination specialist",
            model_provider=model_provider
        )
        
        # Initialize specialized agents
        self.research_agent = ResearchAgent(model_provider)
        self.weather_agent = WeatherAgent(model_provider)
        self.budget_agent = BudgetAgent(model_provider)
        self.itinerary_agent = ItineraryAgent(model_provider)
        
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate the multi-agent travel planning process"""
        user_query = task.get("query", "")
        
        # Parse user requirements
        requirements = await self._parse_user_requirements(user_query)
        
        # Coordinate agents in sequence
        planning_result = await self._coordinate_planning(requirements)
        
        # Generate final comprehensive response
        final_response = await self._generate_final_response(planning_result)
        
        return final_response
        
    async def _parse_user_requirements(self, query: str) -> Dict:
        """Parse user query with better destination extraction"""
        system_prompt = """Extract EXACT travel information from this query:
        
        1. Destination (city/place name exactly as mentioned)
        2. Duration in days
        3. Budget level if mentioned
        4. Number of travelers
        
        Focus on the EXACT destination mentioned. Do NOT assume or change the location.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract info from: '{query}'")
        ]
        
        try:
            analysis = await self._safe_llm_call(messages)
            analysis_content = analysis.content
        except Exception as e:
            analysis_content = f"Error in parsing: {str(e)}"
        
        
        destination_patterns = [
            r'trip (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
            r'visit ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)', 
            r'travel (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
            r'go (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
            r'(\d+) day[s]? trip (?:to|in) ([A-Za-z\s,]+)',
            r'(\d+) day[s]? (?:in|at) ([A-Za-z\s,]+)',
            r'(?:in|at) ([A-Za-z\s,]+?) for \d+ day[s]?'
        ]
        
        destination = "Unknown"
        query_lower = query.lower()
        
        print(f"🔍 Parsing query: '{query}'")
        
        for i, pattern in enumerate(destination_patterns):
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:  # Pattern with duration and destination
                    destination = match.group(2).strip().title()
                else:
                    destination = match.group(1).strip().title()
                
                destination = re.sub(r'\s+', ' ', destination).strip()
                print(f"Found destination: '{destination}' using pattern {i+1}")
                break
            
        # Extract duration
        duration_match = re.search(r'(\d+)\s*day[s]?', query_lower)
        duration = int(duration_match.group(1)) if duration_match else 5
        
        print(f" Final parsed - Destination: '{destination}', Duration: {duration} days")
        
        return {
            "original_query": query,
            "destination": destination,
            "duration": duration,
            "analysis": analysis_content
        }
        
    
    async def _coordinate_planning(self, requirements: Dict) -> Dict:
        """Coordinate all agents to plan the trip"""
        destination = requirements.get("destination")
        duration = requirements.get("duration", 5)
        
        print(f"🤖 Starting multi-agent planning for {destination} ({duration} days)...")
        
        # Phase 1: Research & Weather (Parallel)
        print("📊 Phase 1: Research and Weather Analysis...")
        research_task = {
            "type": "destination_research",
            "destination": destination,
            "duration": f"{duration} days"
        }
        
        weather_task = {
            "type": "forecast",
            "destination": destination
        }
        
        # Run research and weather agents in parallel
        research_result, weather_result = await asyncio.gather(
            self.research_agent.process(research_task),
            self.weather_agent.process(weather_task)
        )
        
        print("✅ Research and Weather completed")
        
        # Phase 2: Budget Planning
        print("💰 Phase 2: Budget Planning...")
        budget_task = {
            "type": "estimate_budget",
            "destination": destination,
            "duration": duration,
            "budget_level": "medium",
            "travelers": 1
        }
        
        budget_result = await self.budget_agent.process(budget_task)
        print("✅ Budget planning completed")
        
        # Phase 3: Itinerary Creation
        print("📅 Phase 3: Itinerary Creation...")
        itinerary_task = {
            "type": "create_itinerary",
            "destination": destination,
            "duration": duration,
            "attractions": research_result.get("research_data", ""),
            "weather_info": weather_result.get("weather_analysis", ""),
            "budget_info": budget_result.get("budget_breakdown", "")
        }
        
        itinerary_result = await self.itinerary_agent.process(itinerary_task)
        print("✅ Itinerary creation completed")
        
        return {
            "research": research_result,
            "weather": weather_result,
            "budget": budget_result,
            "itinerary": itinerary_result,
            "coordination_status": "completed"
        }
        
    async def _generate_final_response(self, planning_result: Dict) -> Dict:
        """Generate comprehensive final response"""
        system_prompt = """You are a master travel planning coordinator. Combine all the specialized agent outputs into a comprehensive, well-structured travel plan.
        
        Structure the response as a complete travel guide:
        
        #  Complete Travel Plan
        
        ## 📍 Destination Overview
        [Destination highlights and key information]
        
        ## 🌤️ Weather Advisory
        [Weather information and recommendations]
        
        ## 💰 Budget Overview
        [Complete budget breakdown with daily estimates]
        
        ## 📅 Detailed Itinerary
        [Day-by-day comprehensive schedule]
        
        ## 🎯 Key Recommendations
        [Important tips, local customs, and must-know information]
        
        ## 📋 Travel Checklist
        [What to pack, documents needed, preparation tips]
        
        Make it engaging, informative, and actionable. Include specific details like costs, timings, and practical advice."""
        
        # Combine all agent outputs
        combined_data = {
            "research": planning_result.get("research", {}).get("research_data", ""),
            "weather": planning_result.get("weather", {}).get("weather_analysis", ""),
            "budget": planning_result.get("budget", {}).get("budget_breakdown", ""),
            "itinerary": planning_result.get("itinerary", {}).get("itinerary", "")
        }
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Combine these agent outputs into final comprehensive travel plan: {combined_data}")
        ]
        
        final_response = await self.llm.ainvoke(messages)
        
        return {
            "agent": self.name,
            "task_type": "comprehensive_travel_plan",
            "final_plan": final_response.content,
            "agent_contributions": {
                "research_agent": planning_result.get("research", {}),
                "weather_agent": planning_result.get("weather", {}),
                "budget_agent": planning_result.get("budget", {}),
                "itinerary_agent": planning_result.get("itinerary", {})
            },
            "status": "completed"
        }