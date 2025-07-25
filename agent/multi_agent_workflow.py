from .coordinator_agent import CoordinatorAgent
from typing import Dict, Any

class MultiAgentWorkflow:
    """Main workflow orchestrator for multi-agent travel planning"""
    
    def __init__(self, model_provider: str = "groq"):
        self.coordinator = CoordinatorAgent(model_provider)
        
    async def plan_trip(self, user_query: str) -> Dict[str, Any]:
        """Main entry point for multi-agent trip planning"""
        
        print("🚀 Starting Multi-Agent Travel Planning System...")
        print(f"📝 User Query: {user_query}")
        print("=" * 60)
        
        # Start coordination process
        task = {"query": user_query}
        result = await self.coordinator.process(task)
        
        print("=" * 60)
        print(" Multi-Agent Planning Completed!")
        
        return result
        
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        return {
            "coordinator": self.coordinator.name,
            "research_agent": self.coordinator.research_agent.name,
            "weather_agent": self.coordinator.weather_agent.name,
            "budget_agent": self.coordinator.budget_agent.name,
            "itinerary_agent": self.coordinator.itinerary_agent.name,
            "total_agents": 5,
            "status": "active"
        }