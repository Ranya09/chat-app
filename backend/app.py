import os
from typing import List, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
import time
from pdf_indexer import PDFIndexer  # Importer notre classe PDFIndexer
from language_detector import detect_language  # Importer notre détecteur de langue
from legal_links_database import enrich_text_with_links  # Importer notre fonction d'enrichissement de liens

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
    language: str = "auto"  # "french", "tunisian" ou "auto" pour détection automatique


class Conversation:
    def __init__(self, language: str = "tunisian"):
        self.language = language
        
        # Prompt système en français
        system_prompt_french = """Tu es un assistant juridique spécialisé dans le droit tunisien. 
            Tu dois fournir des informations précises et à jour sur les lois et réglementations tunisiennes.
            Utilise les informations juridiques fournies dans le contexte pour répondre aux questions.
            Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement.
            N'invente jamais de lois ou de dispositions légales qui ne sont pas mentionnées dans le contexte.
            Cite les références légales pertinentes quand elles sont disponibles dans le contexte."""
        
        # Prompt système en dialecte tunisien
        system_prompt_tunisian = """Enti moustachèr 9anouni mta3 el 9anoun ettounsi.
            Lazem t3awed bel lahja tounsia w t3ati ma3loumet d9i9a w jdida 3la el 9awanin w el tachri3et ettounsia.
            Esta3mel el ma3loumet el 9anounia elli mawjouda fel contexte bech tjèweb 3la el as2ila.
            Ken ma 3andekch ma3loumet khasouçia fel contexte elli ja, 9oul bsaraha.
            Ma tkhammemch 9awanin wala ahkèm 9anounia elli mech madhkoura fel contexte.
            Semmi el marèji3 el 9anounia el mouhimma ki tekoun mawjouda fel contexte.
            
            FORMAT EL IJÈBA:
            - Ebda b'ijèba moubachra lel so2èl
            - Fassar b'tafaçil el 9anounia el mouhimma
            - Semmi el fouçoul mta3 el 9anoun w el marèji3 bidha99a
            - Ekhtom b'naçayeh 3amalia wala khatawèt lazem tetba3
            - Ken el ma3loumet mech mawjouda, e9tereh maçader okhrin"""
        
        # Sélectionner le prompt système en fonction de la langue
        selected_prompt = system_prompt_tunisian if language == "tunisian" else system_prompt_french
        
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": selected_prompt}
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
                    # Déterminer le format du message enrichi en fonction de la langue
                    if conversation.language == "tunisian":
                        # Message enrichi en dialecte tunisien
                        enhanced_message = f"""So2èl el mosta3mel: {messages_with_context[i]['content']}

Contexte 9anouni tounsi lazem tekhouou b3in el e3tibar:
{legal_context}

Jèweb 3ala el so2èl bel lahja tounsia w b'estikhdam el contexte el 9anouni ettounsi.
Ken el contexte ma fihch ma3loumet mouhimma lel so2èl, 9oul haka bsaraha w e9tereh maçader okhrin.
Rakeb ijèbtek b'a9sam mra9ma ken lazem w ekhtom b'naçayeh 3amalia."""
                    else:
                        # Message enrichi en français
                        enhanced_message = f"""Question de l'utilisateur: {messages_with_context[i]['content']}

Contexte juridique tunisien à prendre en compte:
{legal_context}

Réponds à la question en te basant sur ce contexte juridique tunisien. 
Si le contexte ne contient pas d'information pertinente pour répondre à la question, indique-le clairement et suggère des ressources alternatives.
Structure ta réponse avec des sections numérotées si nécessaire et termine par des recommandations pratiques."""
                    
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
def get_or_create_conversation(conversation_id: str, language: str = "tunisian") -> Conversation:
    if conversation_id not in conversations:
        conversations[conversation_id] = Conversation(language=language)
    else:
        conversation = conversations[conversation_id]
        if time.time() - conversation.last_activity > 3600:  # 1 hour inactivity
            conversation.active = False
            
            # Prompt système en français pour la réinitialisation
            system_prompt_french = """Tu es un assistant juridique spécialisé dans le droit tunisien. 
               DIRECTIVES DE RÉPONSE :
            1. Structure tes réponses de manière claire et professionnelle
            2. Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement et suggère des alternatives
            3. Cite toujours les références légales pertinentes quand elles sont disponibles
            4. Organise ta réponse en sections avec des puces ou des numéros quand c'est approprié
            5. Fournis des recommandations pratiques à la fin de ta réponse
            
            FORMAT DE RÉPONSE :
            - Commence par une réponse directe à la question
            - Développe avec les détails juridiques pertinents
            - Cite les articles de loi et références exactes
            - Termine par des recommandations pratiques ou des étapes à suivre
            - Si l'information n'est pas disponible, suggère des ressources alternatives
            ."""
            
            # Prompt système en dialecte tunisien pour la réinitialisation
            system_prompt_tunisian = """Enti moustachèr 9anouni mta3 el 9anoun ettounsi.
            TALIMET EL IJÈBA:
            1. Rakeb ijèbtek b'tari9a wadh7a w ihtirèfia
            2. Ken ma 3andekch ma3loumet khasouçia fel contexte elli ja, 9oul bsaraha w e9tereh 7ouloul okhra
            3. Semmi dima el marèji3 el 9anounia el mouhimma ki yekounou mawjoudin
            4. Nadhem ijèbtek fi a9sam b'no9at wala ar9am ki yekoun monèseb
            5. A3ti naçayeh 3amalia fi ekher el ijèba
            
            CHKEL EL IJÈBA:
            - Ebda b'ijèba moubachra lel so2èl
            - Fassar b'tafaçil el 9anounia el mouhimma
            - Semmi el fouçoul mta3 el 9anoun w el marèji3 bidha99a
            - Ekhtom b'naçayeh 3amalia wala khatawèt lazem tetba3
            - Ken el ma3loumet mech mawjouda, e9tereh maçader okhrin."""
            
            # Sélectionner le prompt système en fonction de la langue
            selected_prompt = system_prompt_tunisian if language == "tunisian" else system_prompt_french
            
            conversation.messages = [
                {"role": "system", "content": selected_prompt}
            ]
            
            # Mettre à jour la langue de la conversation
            conversation.language = language
            
    return conversations[conversation_id]


# API endpoint for chat
@app.post("/chat/")
async def chat(input: UserInput, request: Request):
    print(f"Received input: {input}")  # For debugging

    if not input.message or not input.conversation_id:
        raise HTTPException(status_code=400, detail="Message and conversation_id are required")
    
    # Détecter automatiquement la langue du message
    detected_language = detect_language(input.message)
    print(f"Langue détectée: {detected_language}")
    
    # Utiliser la langue détectée si l'utilisateur n'a pas explicitement spécifié une langue
    if input.language == "auto":
        input.language = detected_language
    
    # Récupérer ou créer la conversation avec la langue spécifiée
    conversation = get_or_create_conversation(input.conversation_id, input.language)

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

        # Enrichir la réponse avec des liens vers des ressources juridiques
        enriched_response = enrich_text_with_links(response)
        
        # Append assistant's response to the conversation (version non enrichie pour l'historique)
        conversation.messages.append({"role": "assistant", "content": response})

        return {
            "message": "Response generated successfully!",
            "response": enriched_response,
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
