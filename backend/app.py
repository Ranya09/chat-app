import os
import re
import time
from typing import List, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
from pdf_indexer import PDFIndexer  # Importer notre classe PDFIndexer améliorée

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

# Système de cache simple
class ResponseCache:
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, key):
        if key in self.cache:
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def set(self, key, value):
        # Si le cache est plein, supprimer l'élément le moins récemment utilisé
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def clear(self):
        self.cache.clear()
        self.access_times.clear()

# Initialiser le cache
response_cache = ResponseCache(max_size=100)

# Data models
class UserInput(BaseModel):
    message: str
    role: str = "user"
    conversation_id: str

class FeedbackInput(BaseModel):
    conversation_id: str
    message_id: str
    rating: int  # 1-5
    comment: str = ""

class DocumentRequest(BaseModel):
    document_type: str  # "lettre_mise_en_demeure", "requete_simple", "procuration", etc.
    language: str = "fr"  # "fr" ou "ar"
    parameters: dict  # Paramètres spécifiques au type de document

class Conversation:
    def __init__(self):
        self.messages: List[Dict[str, str]] = [
            {"role": "system", "content": """Tu es un assistant juridique spécialisé dans le droit tunisien, capable de répondre en français et en arabe.

DIRECTIVES GÉNÉRALES :
1. Détecte automatiquement la langue de l'utilisateur (français ou arabe) et réponds dans la même langue
2. Justifie toujours tes réponses avec des références précises aux lois, codes et articles tunisiens
3. Structure tes réponses de manière claire et professionnelle
4. Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement
5. N'invente jamais de lois ou de dispositions légales qui ne sont pas mentionnées dans le contexte

FORMAT DE RÉPONSE EN FRANÇAIS :
- Commence par une réponse directe à la question
- Développe avec les détails juridiques pertinents
- Cite explicitement les articles de loi et références exactes (ex: "Selon l'article 123 du Code du Travail tunisien...")
- Termine par des recommandations pratiques ou des étapes à suivre

تنسيق الإجابة بالعربية:
- ابدأ بإجابة مباشرة على السؤال
- قم بتطوير إجابتك مع التفاصيل القانونية ذات الصلة
- استشهد صراحة بمواد القانون والمراجع الدقيقة (مثال: "وفقًا للمادة 123 من مجلة الشغل التونسية...")
- اختم بتوصيات عملية أو خطوات يجب اتباعها

Utilise les informations juridiques fournies dans le contexte pour répondre aux questions."""}
        ]
        self.active: bool = True
        self.last_activity: float = time.time()

    def update_last_activity(self):
        self.last_activity = time.time()


# In-memory conversation storage (for demonstration purposes)
conversations: Dict[str, Conversation] = {}


# Fonction simple de détection de langue
def detect_language(text: str) -> str:
    # Caractères arabes courants
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    
    # Si le texte contient des caractères arabes, on considère qu'il est en arabe
    if arabic_pattern.search(text):
        return "arabic"
    else:
        return "french"  # Par défaut, on considère que c'est du français


# Groq API interaction function with context enhancement and language detection
def query_groq_api(conversation: Conversation, user_query: str) -> str:
    try:
        # Générer une clé de cache basée sur la requête et les derniers messages
        # Limiter à 3 derniers messages pour éviter des clés trop longues
        last_messages = conversation.messages[-3:] if len(conversation.messages) > 3 else conversation.messages
        cache_key = f"{user_query}_{str(last_messages)}"
        
        # Vérifier si la réponse est dans le cache
        cached_response = response_cache.get(cache_key)
        if cached_response:
            print("Réponse trouvée dans le cache")
            return cached_response
            
        # Détecter la langue de la requête
        language = detect_language(user_query)
        print(f"Langue détectée: {language}")
        
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
                    # Ajouter le contexte juridique en fonction de la langue détectée
                    if language == "arabic":
                        enhanced_message = f"""سؤال المستخدم: {messages_with_context[i]['content']}

السياق القانوني التونسي الذي يجب مراعاته:
{legal_context}

أجب على السؤال بناءً على هذا السياق القانوني التونسي.
يجب أن تستشهد دائمًا بمواد القانون والمراجع الدقيقة (مثال: "وفقًا للمادة 123 من مجلة الشغل التونسية...").
إذا كان السياق لا يحتوي على معلومات ذات صلة للإجابة على السؤال، فأشر إلى ذلك بوضوح واقترح موارد بديلة.
قم بهيكلة إجابتك بأقسام مرقمة إذا لزم الأمر وانتهِ بتوصيات عملية.
أجب باللغة العربية."""
                    else:  # french
                        enhanced_message = f"""Question de l'utilisateur: {messages_with_context[i]['content']}

Contexte juridique tunisien à prendre en compte:
{legal_context}

Réponds à la question en te basant sur ce contexte juridique tunisien.
Tu dois toujours citer explicitement les articles de loi et références exactes (ex: "Selon l'article 123 du Code du Travail tunisien...").
Si le contexte ne contient pas d'information pertinente pour répondre à la question, indique-le clairement et suggère des ressources alternatives.
Structure ta réponse avec des sections numérotées si nécessaire et termine par des recommandations pratiques.
Réponds en français."""
                    
                    # Remplacer le message original par le message enrichi
                    messages_with_context[i]["content"] = enhanced_message
                    print(f"Message enrichi avec contexte juridique en {language}")
                    break
        else:
            # Si aucun contexte n'est trouvé, ajouter une instruction pour répondre dans la langue détectée
            for i in range(len(messages_with_context) - 1, -1, -1):
                if messages_with_context[i]["role"] == "user":
                    # Ajouter l'instruction de répondre dans la langue détectée
                    if language == "arabic":
                        enhanced_message = f"""سؤال المستخدم: {messages_with_context[i]['content']}

لم يتم العثور على معلومات محددة في قاعدة البيانات القانونية.
يرجى الإجابة على السؤال بأفضل ما لديك من معرفة عامة حول القانون التونسي.
يجب أن تستشهد دائمًا بمواد القانون والمراجع الدقيقة إذا كنت تعرفها.
أجب باللغة العربية."""
                    else:  # french
                        enhanced_message = f"""Question de l'utilisateur: {messages_with_context[i]['content']}

Aucune information spécifique n'a été trouvée dans la base de données juridique.
Réponds à la question avec ta meilleure connaissance générale du droit tunisien.
Tu dois toujours citer explicitement les articles de loi et références exactes si tu les connais.
Réponds en français."""
                    
                    # Remplacer le message original par le message enrichi
                    messages_with_context[i]["content"] = enhanced_message
                    print(f"Message enrichi avec instruction de répondre en {language}")
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
        
        # Stocker la réponse dans le cache
        response_cache.set(cache_key, response)

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
                {"role": "system", "content": """Tu es un assistant juridique spécialisé dans le droit tunisien, capable de répondre en français et en arabe.

DIRECTIVES GÉNÉRALES :
1. Détecte automatiquement la langue de l'utilisateur (français ou arabe) et réponds dans la même langue
2. Justifie toujours tes réponses avec des références précises aux lois, codes et articles tunisiens
3. Structure tes réponses de manière claire et professionnelle
4. Si tu n'as pas d'information spécifique dans le contexte fourni, précise-le clairement
5. N'invente jamais de lois ou de dispositions légales qui ne sont pas mentionnées dans le contexte

FORMAT DE RÉPONSE EN FRANÇAIS :
- Commence par une réponse directe à la question
- Développe avec les détails juridiques pertinents
- Cite explicitement les articles de loi et références exactes (ex: "Selon l'article 123 du Code du Travail tunisien...")
- Termine par des recommandations pratiques ou des étapes à suivre

تنسيق الإجابة بالعربية:
- ابدأ بإجابة مباشرة على السؤال
- قم بتطوير إجابتك مع التفاصيل القانونية ذات الصلة
- استشهد صراحة بمواد القانون والمراجع الدقيقة (مثال: "وفقًا للمادة 123 من مجلة الشغل التونسية...")
- اختم بتوصيات عملية أو خطوات يجب اتباعها

Utilise les informations juridiques fournies dans le contexte pour répondre aux questions."""}
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

        # Query Groq API with enhanced context and language detection
        response = query_groq_api(conversation, input.message)

        # Append assistant's response to the conversation
        conversation.messages.append({"role": "assistant", "content": response})

        # Détecter la langue de la réponse pour informer le frontend
        response_language = detect_language(response)

        return {
            "message": "Response generated successfully!",
            "response": response,
            "conversation_id": input.conversation_id,
            "language": response_language  # Ajouter la langue détectée à la réponse
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


# Endpoint pour vider le cache
@app.post("/clear_cache/")
async def clear_cache():
    response_cache.clear()
    return {"message": "Cache vidé avec succès"}


# Endpoint pour recevoir le feedback
@app.post("/feedback/")
async def submit_feedback(feedback: FeedbackInput):
    try:
        # Créer un répertoire pour stocker les feedbacks s'il n'existe pas
        feedback_dir = "feedback_data"
        if not os.path.exists(feedback_dir):
            os.makedirs(feedback_dir)
        
        # Enregistrer le feedback dans un fichier CSV
        feedback_file = os.path.join(feedback_dir, "feedback_log.csv")
        
        # Créer l'en-tête si le fichier n'existe pas
        if not os.path.exists(feedback_file):
            with open(feedback_file, "w", encoding="utf-8") as f:
                f.write("timestamp,conversation_id,message_id,rating,comment\n")
        
        # Ajouter le feedback au fichier
        with open(feedback_file, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            # Échapper les virgules et les sauts de ligne dans le commentaire
            safe_comment = feedback.comment.replace(",", "\\,").replace("\n", "\\n")
            f.write(f"{timestamp},{feedback.conversation_id},{feedback.message_id},{feedback.rating},{safe_comment}\n")
        
        return {"message": "Feedback enregistré avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint pour obtenir les statistiques de feedback
@app.get("/feedback/stats/")
async def get_feedback_stats():
    try:
        feedback_file = os.path.join("feedback_data", "feedback_log.csv")
        
        if not os.path.exists(feedback_file):
            return {"message": "Aucun feedback disponible", "stats": {}}
        
        # Lire le fichier CSV et calculer les statistiques
        ratings = []
        with open(feedback_file, "r", encoding="utf-8") as f:
            # Ignorer l'en-tête
            next(f)
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    try:
                        rating = int(parts[3])
                        ratings.append(rating)
                    except ValueError:
                        continue
        
        if not ratings:
            return {"message": "Aucun feedback disponible", "stats": {}}
        
        # Calculer les statistiques
        avg_rating = sum(ratings) / len(ratings)
        rating_counts = {i: ratings.count(i) for i in range(1, 6)}
        
        return {
            "message": "Statistiques de feedback récupérées avec succès",
            "stats": {
                "total_feedbacks": len(ratings),
                "average_rating": avg_rating,
                "rating_distribution": rating_counts
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint pour générer des documents juridiques
@app.post("/generate_document/")
async def generate_document(request: DocumentRequest):
    try:
        # Vérifier si le type de document est supporté
        supported_types = ["lettre_mise_en_demeure", "requete_simple", "procuration"]
        if request.document_type not in supported_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Type de document non supporté. Types supportés: {', '.join(supported_types)}"
            )
        
        # Vérifier la langue
        if request.language not in ["fr", "ar"]:
            raise HTTPException(status_code=400, detail="Langue non supportée. Langues supportées: fr, ar")
        
        # Charger le template approprié
        template_dir = "document_templates"
        template_file = os.path.join(template_dir, f"{request.document_type}_{request.language}.txt")
        
        if not os.path.exists(template_file):
            raise HTTPException(status_code=404, detail="Template de document non trouvé")
        
        # Lire le template
        with open(template_file, "r", encoding="utf-8") as f:
            template = f.read()
        
        # Remplacer les variables dans le template
        for key, value in request.parameters.items():
            placeholder = f"{{{{{key}}}}}"
            template = template.replace(placeholder, str(value))
        
        # Générer un nom de fichier unique
        timestamp = time.strftime("%Y%m%d%H%M%S")
        filename = f"{request.document_type}_{request.language}_{timestamp}.txt"
        output_dir = "generated_documents"
        
        # Créer le répertoire s'il n'existe pas
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Enregistrer le document généré
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(template)
        
        # Retourner le document généré
        return {
            "message": "Document généré avec succès",
            "document_content": template,
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint pour obtenir la liste des templates disponibles
@app.get("/document_templates/")
async def get_document_templates():
    try:
        template_dir = "document_templates"
        if not os.path.exists(template_dir):
            return {"templates": []}
        
        templates = []
        for file in os.listdir(template_dir):
            if file.endswith(".txt"):
                parts = file.split("_")
                if len(parts) >= 2:
                    doc_type = parts[0]
                    language = parts[1].split(".")[0]
                    templates.append({
                        "type": doc_type,
                        "language": language,
                        "filename": file
                    })
        
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------ Nouvel Endpoint d'Upload de Document ------

@app.post("/upload_document/")
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: str = Form(...),
    language: str = Form(...)
):
    try:
        upload_dir = "uploaded_documents"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        file_location = os.path.join(upload_dir, file.filename)
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
        # Ici, vous pouvez intégrer une logique d'analyse du document (ex : PDFIndexer)
        summary = f"Résumé du fichier {file.filename}"  # Exemple de résumé
        return {"summary": summary, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lancer l'application (si exécuté directement)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
