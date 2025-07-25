from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.multi_agent_workflow import MultiAgentWorkflow  # Changed import
from utils.save_to_document import save_document
from starlette.responses import JSONResponse
import os
import datetime
import re
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio

load_dotenv()

app = FastAPI(title="Ninja Navigator AI - Multi-Agent Travel Planner")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

def extract_destination_from_query(query: str) -> str:
    """Extract destination from user query - IMPROVED VERSION"""
    query_lower = query.lower().strip()
    
    # More comprehensive patterns to catch destinations
    patterns = [
        r'trip (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
        r'visit ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
        r'travel (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
        r'go (?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
        r'plan.*?(?:to|in) ([A-Za-z\s,]+?)(?:\s+for|\s+\d+|$)',
        r'(\d+) day[s]? trip (?:to|in) ([A-Za-z\s,]+)',
        r'(\d+) day[s]? (?:in|at) ([A-Za-z\s,]+)',
        r'(?:in|at) ([A-Za-z\s,]+?) for \d+ day[s]?',
        r'([A-Za-z\s,]+?) (?:for|in) \d+ day[s]?'
    ]
    
    print(f"🔍 Parsing query: '{query}'")
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:  # Pattern with both duration and destination
                destination = match.group(2).strip().title()
            else:
                destination = match.group(1).strip().title()
            
            # Clean up the destination
            destination = re.sub(r'\s+', ' ', destination)  # Remove extra spaces
            destination = destination.replace(',', '').strip()
            
            print(f" Found destination using pattern {i+1}: '{destination}'")
            return destination
    
    # Fallback: Look for any proper noun-like words
    words = query.split()
    for word in words:
        if word[0].isupper() and len(word) > 2 and word.lower() not in ['plan', 'trip', 'day', 'days', 'for', 'the', 'and']:
            print(f" Fallback destination found: '{word}'")
            return word
    
    print("❌ No destination found, using 'Unknown'")
    return "Unknown_Destination"

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Ninja Navigator AI - Multi-Agent Travel Planning System",
        "status": "active",
        "version": "2.0.0"
    }

@app.post("/query")
async def query_travel_agent(query: QueryRequest):
    """Endpoint to handle queries for the multi-agent travel system."""
    try:
        print(f"🎯 Received query: '{query.question}'")
        
        # Extract destination FIRST for verification FOR the multi-agent system
        destination = extract_destination_from_query(query.question)
        print(f"📍 Extracted destination: '{destination}'")
        
        # Initialize multi-agent workflow
        workflow = MultiAgentWorkflow(model_provider="groq")
        
        # Process with multi-agent system
        result = await workflow.plan_trip(query.question)
        
        # Verify the result is for the correct destination
        final_output = result.get("final_plan", "No response generated")
        
        # Double-check if the response mentions the correct destination
        if destination.lower() not in final_output.lower() and destination != "Unknown_Destination":
            print(f"⚠️ WARNING: Response may not be for {destination}")
            # Add a note to clarify
            final_output = f"# Travel Plan for {destination}\n\n{final_output}"
        
        # Save the document with the destination in the filename
        saved_file = save_document(final_output, destination)
        
        if saved_file:
            print(f"📄 Travel Plan saved as: {saved_file}")
        
        return {
            "answer": final_output,
            "destination_extracted": destination,  # Add this for debugging
            "agent_contributions": result.get("agent_contributions", {}),
            "planning_status": "completed",
            "agents_involved": workflow.get_agent_status()
        }
        
    except Exception as e:
        print(f" Error: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents in the system"""
    workflow = MultiAgentWorkflow()
    return workflow.get_agent_status()

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "system": "Multi-Agent AI Travel Planning",
        "agents": 5
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)