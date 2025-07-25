from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document
from starlette.responses import JSONResponse
import os
import datetime
import re
from dotenv import load_dotenv
from pydantic import BaseModel
from utils.save_to_document import save_document
load_dotenv()

app = FastAPI()

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
    """Extract destination from user query"""
    query_lower = query.lower()
    
    # Common patterns to extract destination
    patterns = [
        r'trip to (\w+)',
        r'visit (\w+)',
        r'travel to (\w+)',
        r'go to (\w+)',
        r'plan.*?(\w+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            return match.group(1).title()
    
    return "Unknown_Destination"

@app.post("/query")
async def query_travel_agent(query:QueryRequest):
    """Endpoint to handle queries for the travel agent."""
    try:
        print(query)
        graph = GraphBuilder(model_provider="groq")
        react_app=graph()
        #react_app = graph.build_graph()

        png_graph = react_app.get_graph().draw_mermaid_png()
        with open("my_graph.png", "wb") as f:
            f.write(png_graph)

        print(f"Graph saved as 'my_graph.png' in {os.getcwd()}")
        
        # Assuming request is a pydantic object like: {"question": "your text"}
        messages={"messages": [query.question]}
        output = react_app.invoke(messages)

        # If result is dict with messages:
        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content  # Last AI response
            # Save the document
            destination= extract_destination_from_query(query.question)

            saved_file = save_document(final_output,destination)
            if saved_file:
                print(f"Travel Plan saved successfully as {saved_file}")
            else:
                print("Failed to save travel plan. Please try again later.")
        else:
            final_output = str(output)
        
        return {"answer": final_output}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})