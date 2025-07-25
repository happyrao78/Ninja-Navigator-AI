from .base_agent import BaseAgent
from typing import Dict, Any
from langchain.schema import HumanMessage, SystemMessage
from utils.currency_converter import CurrencyConverter
from utils.expense_calculator import Calculator
import os

class BudgetAgent(BaseAgent):
    """Agent specialized in budget planning and cost estimation"""
    
    def __init__(self, model_provider: str = "groq"):
        super().__init__(
            name="Budget Agent",
            role="Travel budget planning and cost estimation specialist",
            model_provider=model_provider
        )
        self.currency_service = CurrencyConverter(os.getenv('EXCHANGE_RATE_API_KEY'))
        self.calculator = Calculator()
        
    async def process(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process budget-related tasks"""
        task_type = task.get("type", "estimate_budget")
        
        if task_type == "currency_conversion":
            return await self._convert_currency(task)
        elif task_type == "cost_breakdown":
            return await self._create_cost_breakdown(task)
        else:
            return await self._estimate_budget(task)
            
    async def _estimate_budget(self, task: Dict) -> Dict:
        """Estimate budget for the trip"""
        destination = task.get("destination")
        duration = task.get("duration", 5)
        budget_level = task.get("budget_level", "medium")
        travelers = task.get("travelers", 1)
        
        system_prompt = f"""You are a travel budget specialist. Create a detailed budget estimate for:
        
        Destination: {destination}
        Duration: {duration} days
        Budget Level: {budget_level}
        Number of Travelers: {travelers}
        
        Provide budget breakdown for:
        1. Accommodation (per night and total)
        2. Food & Dining (daily estimates)
        3. Transportation (local and to/from destination)
        4. Activities & Attractions
        5. Shopping & Miscellaneous
        6. Emergency buffer (10-15%)
        
        Give both daily and total estimates in USD. Be realistic and research-based.
        Include specific cost ranges for {budget_level} budget level."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create detailed budget estimate for {destination} trip")
        ]
        
        budget_analysis = await self.llm.ainvoke(messages)
        
        return {
            "agent": self.name,
            "task_type": "budget_estimate",
            "destination": destination,
            "duration": duration,
            "budget_breakdown": budget_analysis.content,
            "status": "completed"
        }
        
    async def _convert_currency(self, task: Dict) -> Dict:
        """Convert currency for budget planning"""
        from_currency = task.get("from_currency", "USD")
        to_currency = task.get("to_currency")
        amount = task.get("amount", 1000)
        
        try:
            converted_amount = self.currency_service.convert(amount, from_currency, to_currency)
            
            return {
                "agent": self.name,
                "task_type": "currency_conversion",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "original_amount": amount,
                "converted_amount": converted_amount,
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "agent": self.name,
                "task_type": "currency_conversion",
                "error": str(e),
                "status": "failed"
            }
            
    async def _create_cost_breakdown(self, task: Dict) -> Dict:
        """Create detailed cost breakdown"""
        costs = task.get("costs", {})
        duration = task.get("duration", 5)
        
        # Calculate totals using calculator
        total_accommodation = costs.get("accommodation", 0) * duration
        total_food = costs.get("food_per_day", 0) * duration
        total_transport = costs.get("transport", 0)
        total_activities = costs.get("activities", 0)
        total_misc = costs.get("miscellaneous", 0)
        
        grand_total = self.calculator.calculate_total(
            total_accommodation, total_food, total_transport, total_activities, total_misc
        )
        
        daily_budget = self.calculator.calculate_daily_budget(grand_total, duration)
        
        breakdown = {
            "accommodation_total": total_accommodation,
            "food_total": total_food,
            "transport_total": total_transport,
            "activities_total": total_activities,
            "miscellaneous_total": total_misc,
            "grand_total": grand_total,
            "daily_budget": daily_budget
        }
        
        return {
            "agent": self.name,
            "task_type": "cost_breakdown",
            "breakdown": breakdown,
            "status": "completed"
        }