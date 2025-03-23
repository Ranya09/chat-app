import os
from typing import List, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
import time

# Load environment variables from .env file
load_dotenv()

# Get Groq API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Check if the API key is available
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

# Initialize FastAPI application
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development).  Change in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)


# Data models
class UserInput(BaseModel):
    message: str
    role: str = "user"
    conversation_id: str


class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]
        self.active: bool = True
        self.last_activity: float = time.time()

    def update_last_activity(self):
        self.last_activity = time.time()


# In-memory conversation storage (for demonstration purposes)
conversations: Dict[str, Conversation] = {}


# Groq API interaction function
def query_groq_api(conversation: Conversation) -> str:
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversation.messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False, # changed from True to false
            stop=None,
        )

        # Access the content safely
        response = completion.choices[0].message.content

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with Groq API: {str(e)}")


# Conversation management functions
def get_or_create_conversation(conversation_id: str) -> Conversation:
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation()
    else:
        conversation = conversations[conversation_id]
        if time.time() - conversation.last_activity > 3600:  # 1 hour inactivity
            conversation.active = False
            conversation.messages = [
                {"role": "system", "content": "You are a helpful AI assistant."}
            ]
    return conversations[conversation_id]


# API endpoint for chat
@app.post("/chat/")
async def chat(input: UserInput, request: Request):
    print(f"Received input: {input}")  # For debugging

    if not input.message or not input.conversation_id:
        raise HTTPException(status_code=400, detail="Message and conversation_id are required")

    conversation = get_or_create_conversation(input.conversation_id)

    if not conversation.active:
        raise HTTPException(
            status_code=400,
            detail="The chat session has ended. Please start a new session.",
        )

    try:
        # Append user message to the conversation
        conversation.messages.append({"role": input.role, "content": input.message})

        conversation.update_last_activity()

        # Query Groq API
        response = query_groq_api(conversation)

        # Append assistant's response to the conversation
        conversation.messages.append({"role": "assistant", "content": response})

        return {
            "message": "Response generated successfully!",
            "response": response,
            "conversation_id": input.conversation_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
