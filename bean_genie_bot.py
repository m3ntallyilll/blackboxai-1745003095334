import os
import json
import time
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set GROQ_API_KEY environment variable directly for testing
os.environ["GROQ_API_KEY"] = "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"

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"  # Using Llama 3.3 70B for best tool use support

# Bot data for simulating responses
conversion_rates = {
    "beans": {
        "diamonds": 2,  # 1 bean = 2 diamonds
        "usd": 0.05     # 1 bean = $0.05
    },
    "diamonds": {
        "beans": 0.5,   # 1 diamond = 0.5 beans
        "usd": 0.025    # 1 diamond = $0.025
    },
    "usd": {
        "beans": 20,    # $1 = 20 beans
        "diamonds": 40  # $1 = 40 diamonds
    }
}

tiers = [
    {"name": "Rookie", "beans": 0, "hours": 0},
    {"name": "Explorer", "beans": 5000, "hours": 60},
    {"name": "Rising Star", "beans": 15000, "hours": 80},
    {"name": "Talent", "beans": 30000, "hours": 100},
    {"name": "Professional", "beans": 60000, "hours": 120},
    {"name": "Elite", "beans": 100000, "hours": 150},
    {"name": "Champion", "beans": 200000, "hours": 180}
]

events = [
    {"name": "Summer Bash", "type": "Contest", "entry_fee": 500, "participants": "12/20", "duration": "5 days", "prize": "10,000 beans"},
    {"name": "Talent Showcase", "type": "Exhibition", "entry_fee": 0, "participants": "8/15", "duration": "3 days", "prize": "Promotion opportunity"},
    {"name": "Team Challenge", "type": "Competition", "entry_fee": 1000, "participants": "24/30", "duration": "7 days", "prize": "25,000 beans + sponsorship"}
]

growth_strategies = {
    "default": "Focus on consistency, engaging with viewers, collaborating with other streamers, and cross-platform promotion.",
    "instagram": "Post daily stories, weekly carousel posts, and use relevant hashtags. Promote your Bigo Live schedule.",
    "tiktok": "Create 3-5 short clips daily from your streams. Use trending sounds and participate in challenges.",
    "youtube": "Upload weekly highlight videos and monthly best-of compilations. Optimize titles and thumbnails.",
    "twitter": "Tweet updates before going live, share screenshots, and engage with your community frequently."
}

import requests
from bs4 import BeautifulSoup
import json
import asyncio
from pyppeteer import launch

async def scrape_onbigo_events() -> str:
    """Scrape official events with rebates from www.onbigo.live"""
    url = "https://www.onbigo.live/events"
    browser = await launch(headless=True, args=['--no-sandbox'])
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle2'})
    
    # Wait for the events container to load - adjust selector as needed
    await page.waitForSelector('.event-list')
    
    # Extract event data
    events = await page.evaluate('''() => {
        const eventElements = document.querySelectorAll('.event-list .event-item');
        const eventData = [];
        eventElements.forEach(event => {
            const name = event.querySelector('.event-name')?.innerText || '';
            const rebate = event.querySelector('.event-rebate')?.innerText || '';
            const entryFee = event.querySelector('.event-entry-fee')?.innerText || '';
            const duration = event.querySelector('.event-duration')?.innerText || '';
            eventData.push({
                name,
                rebate,
                entryFee,
                duration
            });
        });
        return eventData;
    }''')
    
    await browser.close()
    return json.dumps({"events": events})

def get_events() -> str:
    """Get current events from Bigo Live, updated to scrape live data"""
    try:
        events_json = asyncio.get_event_loop().run_until_complete(scrape_onbigo_events())
        return events_json
    except Exception as e:
        return json.dumps({"error": f"Failed to scrape events: {str(e)}"})

def get_sponsorship_info(how_to_get: str = "") -> str:
    """Get strategies on how to obtain sponsors"""
    strategies = [
        "Build a strong and engaged audience by consistently streaming high-quality content.",
        "Network with other streamers and industry professionals to increase visibility.",
        "Create a professional media kit showcasing your audience demographics and engagement.",
        "Reach out to potential sponsors with personalized proposals highlighting mutual benefits.",
        "Leverage social media platforms to promote your streaming brand and attract sponsors.",
        "Participate in community events and collaborations to expand your reach.",
        "Maintain transparency and professionalism in all sponsorship dealings.",
        "Offer unique sponsorship packages tailored to different sponsor needs."
    ]
    return json.dumps({"strategies": strategies})

# Pydantic model for command parsing
class CommandParameters(BaseModel):
    command: str = Field(..., description="The command name without the ! prefix")
    args: Dict[str, Any] = Field(default_factory=dict, description="Command arguments as key-value pairs")

# Define tools for Groq API
tools = [
    {
        "type": "function",
        "function": {
            "name": "parse_command",
            "description": "Parse a Discord bot command and extract command name and arguments",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The command name without the ! prefix (e.g., 'convert', 'track')"
                    },
                    "args": {
                        "type": "object",
                        "description": "Command arguments as key-value pairs",
                        "additionalProperties": {
                            "type": "string"
                        }
                    }
                },
                "required": ["command"]
            }
        }
    }
]

# Map command names to their functions
command_functions = {
    "convert": lambda **kwargs: json.dumps({"response": "Convert command not implemented yet."}),
    "track": lambda **kwargs: json.dumps({"response": "Track command not implemented yet."}),
    "events": get_events,
    "growth": lambda **kwargs: json.dumps({"response": "Growth command not implemented yet."}),
    "sponsorship": get_sponsorship_info,
    "wishlist": lambda **kwargs: json.dumps({"response": "Wishlist command not implemented yet."}),
    "cross_promote": lambda **kwargs: json.dumps({"response": "Cross promote command not implemented yet."}),
    "strategy": lambda **kwargs: json.dumps({"response": "Strategy command not implemented yet."}),
    "event_info": lambda **kwargs: json.dumps({"response": "Event info command not implemented yet."}),
    "join_event": lambda **kwargs: json.dumps({"response": "Join event command not implemented yet."}),
    "loan_info": lambda **kwargs: json.dumps({"response": "Loan info command not implemented yet."}),
    "credit_score": lambda **kwargs: json.dumps({"response": "Credit score command not implemented yet."})
}

# Function to process commands with conversation memory
def process_command(user_input: str, conversation_history: str = "") -> str:
    """Process a user input and intelligently decide which command to run or respond conversationally, using conversation history"""
    system_message = """You are Bean-Genie, a Discord bot for Bigo Live streamers.
    You can understand natural language input and decide which command to run if any.
    If the input is a command, extract the command name and arguments.
    If the input is conversational, respond appropriately without requiring a command prefix.
    Use the conversation history to maintain context.
    """
    
    # Combine conversation history and current user input
    combined_input = conversation_history + "\nUser: " + user_input
    
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": combined_input}
    ]
    
    try:
        # Use the Groq client to get a response that decides what to do
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        
        # Try to parse content as JSON command call
        try:
            parsed = json.loads(content)
            command = parsed.get("command", "").lower()
            args = parsed.get("args", {})
            if command in command_functions:
                return command_functions[command](**args)
            else:
                # If command unknown, return content as is
                return content
        except Exception:
            # If not JSON, return content as conversational response
            return content
        
    except Exception as e:
        return json.dumps({"error": f"Error processing input: {str(e)}"})

# Example usage
def format_response(response):
    """Format the response for display"""
    try:
        data = json.loads(response)
    except Exception:
        return response
    
    if "error" in data:
        return f"❌ Error: {data['error']}"
    
    formatted = []
    for key, value in data.items():
        if isinstance(value, dict):
            formatted.append(f"**{key.replace('_', ' ').title()}:**")
            for k, v in value.items():
                formatted.append(f"  - {k.replace('_', ' ').title()}: {v}")
        elif isinstance(value, list):
            formatted.append(f"**{key.replace('_', ' ').title()}:**")
            for item in value:
                if isinstance(item, dict):
                    for k, v in item.items():
                        formatted.append(f"  - {k.replace('_', ' ').title()}: {v}")
                else:
                    formatted.append(f"  - {item}")
        else:
            formatted.append(f"**{key.replace('_', ' ').title()}:** {value}")
    return "\n".join(formatted)

# CLI application
def run_cli():
    print("Bean-Genie Discord Bot (CLI Version)")
    print("Type a command (e.g., !convert beans 1000) or 'exit' to quit.")
    print("-" * 50)
    
    while True:
        user_input = input("\nEnter command: ")
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        response = process_command(user_input)
        print("\nResponse:")
        print(format_response(response))
        print("-" * 50)

if __name__ == "__main__":
    run_cli()
