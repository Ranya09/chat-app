import os
from typing import List, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
import time
from pdf_indexer import PDFIndexer  # Importer notre classe PDFIndexer

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
    allow_origins=["*"],  # Allow all origins (for development). Change in production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# Initialize PDF indexer
pdf_indexer = PDFIndexer(pdf_directory="legal_documents")
# Indexer les documents au démarrage de l'application
pdf_indexer.index_documents()


# Data models
class UserInput(BaseModel):
    message: str
    role: str = "user"
    conversation_id: str


class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": """Tu es un assistant juridique spécialisé dans le droit tunisien. 
            Tu dois fournir des informations précises et à jour sur les lois et réglementations tunisiennes.
            Utilise les informations juridiques fournies dans le contexte pour répondre aux questions.
            Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement.
            N'invente jamais de lois ou de dispositions légales qui ne sont pas mentionnées dans le contexte.
            Cite les références légales pertinentes quand elles sont disponibles dans le contexte."""}
        ]
        self.active: bool = True
        self.last_activity: float = time.time()

    def update_last_activity(self):
        self.last_activity = time.time()


# In-memory conversation storage (for demonstration purposes)
conversations: Dict[str, Conversation] = {}


# Groq API interaction function with context enhancement and debugging
def query_groq_api(conversation: Conversation, user_query: str) -> str:
    try:
        # Rechercher des informations pertinentes dans les documents juridiques
        print(f"Recherche de contexte pour: {user_query}")
        legal_context = pdf_indexer.get_relevant_context(user_query)
        print(f"Contexte trouvé: {legal_context[:100]}..." if legal_context else "Aucun contexte trouvé")
        
        # Créer une copie des messages pour ne pas modifier l'historique original
        messages_with_context = conversation.messages.copy()
        
        # Ajouter le contexte juridique au message de l'utilisateur si des informations pertinentes ont été trouvées
        if legal_context:
            # Trouver le dernier message de l'utilisateur
            for i in range(len(messages_with_context) - 1, -1, -1):
                if messages_with_context[i]["role"] == "user":
                    # Ajouter le contexte juridique
                    enhanced_message = f"""Question de l'utilisateur: {messages_with_context[i]['content']}

Contexte juridique tunisien à prendre en compte:
{legal_context}

Réponds à la question en te basant sur ce contexte juridique tunisien."""
                    
                    # Remplacer le message original par le message enrichi
                    messages_with_context[i]["content"] = enhanced_message
                    print(f"Message enrichi avec contexte juridique")
                    break
        
        print("Envoi de la requête à Groq...")
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages_with_context,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        print("Réponse reçue de Groq")

        # Access the content safely
        response = completion.choices[0].message.content
        print(f"Réponse générée: {response[:100]}...")

        return response

    except Exception as e:
        print(f"Erreur détaillée dans query_groq_api: {str(e)}")
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
                {"role": "system", "content": """Tu es un assistant juridique spécialisé dans le droit tunisien. 
                Tu dois fournir des informations précises et à jour sur les lois et réglementations tunisiennes.
                Utilise les informations juridiques fournies dans le contexte pour répondre aux questions.
                Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement.
                N'invente jamais de lois ou de dispositions légales qui ne sont pas mentionnées dans le contexte.
                Cite les références légales pertinentes quand elles sont disponibles dans le contexte."""}
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

        # Query Groq API with enhanced context
        response = query_groq_api(conversation, input.message)

        # Append assistant's response to the conversation
        conversation.messages.append({"role": "assistant", "content": response})

        return {
            "message": "Response generated successfully!",
            "response": response,
            "conversation_id": input.conversation_id,
        }

    except Exception as e:
        print(f"Erreur détaillée dans chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint pour réindexer les documents (utile si vous ajoutez de nouveaux documents)
@app.post("/reindex/")
async def reindex_documents():
    try:
        pdf_indexer.index_documents()
        return {"message": "Documents réindexés avec succès!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de test pour vérifier la connexion à Groq
@app.get("/test-groq/")
async def test_groq():
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, how are you?"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        return {"status": "success", "response": completion.choices[0].message.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Run the application
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
