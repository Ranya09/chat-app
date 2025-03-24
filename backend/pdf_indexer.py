import os
import glob
from typing import List, Dict, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class PDFIndexer:
    def __init__(self, pdf_directory: str):
        """
        Initialise l'indexeur de PDF.
        
        Args:
            pdf_directory: Chemin vers le répertoire contenant les fichiers PDF juridiques
        """
        self.pdf_directory = pdf_directory
        self.documents = []  # Liste pour stocker le contenu des documents
        self.document_paths = []  # Liste pour stocker les chemins des documents
        self.vectorizer = None  # Sera initialisé lors de l'indexation
        self.document_vectors = None  # Sera initialisé lors de l'indexation
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extrait le texte d'un fichier PDF en utilisant PyPDF2 (compatible Windows).
        
        Args:
            pdf_path: Chemin vers le fichier PDF
            
        Returns:
            Le texte extrait du PDF
        """
        try:
            import PyPDF2
            
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n\n"
            
            return text
        except Exception as e:
            print(f"Erreur lors de l'extraction du texte de {pdf_path}: {str(e)}")
            return ""
    
    def index_documents(self) -> None:
        """
        Indexe tous les documents PDF dans le répertoire spécifié.
        """
        # Trouver tous les fichiers PDF dans le répertoire
        pdf_files = glob.glob(os.path.join(self.pdf_directory, "*.pdf"))
        
        if not pdf_files:
            print(f"Aucun fichier PDF trouvé dans {self.pdf_directory}")
            return
        
        # Extraire le texte de chaque PDF
        for pdf_path in pdf_files:
            text = self.extract_text_from_pdf(pdf_path)
            if text:
                self.documents.append(text)
                self.document_paths.append(pdf_path)
                print(f"Indexé: {os.path.basename(pdf_path)}")
        
        # Créer un vectoriseur TF-IDF et transformer les documents
        if self.documents:
            # Définir une liste de mots vides français courants
            french_stopwords = [
                "a", "à", "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en", 
                "et", "eux", "il", "ils", "je", "la", "le", "les", "leur", "lui", "ma", "mais", "me", 
                "même", "mes", "moi", "mon", "ni", "notre", "nous", "ou", "par", "pas", "pour", "qu", 
                "que", "qui", "s", "sa", "se", "si", "son", "sur", "ta", "te", "tes", "toi", "ton", 
                "tu", "un", "une", "votre", "vous", "c", "d", "j", "l", "m", "n", "s", "t", "y", "est", 
                "été", "étée", "étées", "étés", "étant", "suis", "es", "est", "sommes", "êtes", "sont", 
                "serai", "seras", "sera", "serons", "serez", "seront", "serais", "serait", "serions", 
                "seriez", "seraient", "étais", "était", "étions", "étiez", "étaient", "fus", "fut", 
                "fûmes", "fûtes", "furent", "sois", "soit", "soyons", "soyez", "soient", "fusse", 
                "fusses", "fût", "fussions", "fussiez", "fussent"
            ]
            
            self.vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words=french_stopwords,  # Utiliser notre liste de mots vides français
                max_df=0.85,
                min_df=2
            )
            self.document_vectors = self.vectorizer.fit_transform(self.documents)
            print(f"Indexation terminée. {len(self.documents)} documents indexés.")
        else:
            print("Aucun document n'a pu être indexé.")
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """
        Recherche les documents les plus pertinents pour une requête donnée.
        
        Args:
            query: La requête de recherche
            top_k: Le nombre de documents à retourner
            
        Returns:
            Une liste de dictionnaires contenant le chemin du document, son contenu et son score
        """
        # Vérifier si l'index a été créé
        if not self.vectorizer or self.document_vectors is None or len(self.documents) == 0:
            print("L'index n'a pas été créé. Veuillez d'abord indexer les documents.")
            return []
        
        # Transformer la requête en vecteur TF-IDF
        query_vector = self.vectorizer.transform([query])
        
        # Calculer la similarité cosinus entre la requête et tous les documents
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        
        # Trier les documents par similarité décroissante
        top_indices = similarities.argsort()[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.0:  # Ne retourner que les documents avec une similarité positive
                results.append({
                    "path": self.document_paths[idx],
                    "content": self.documents[idx][:1000] + "...",  # Tronquer pour éviter des textes trop longs
                    "score": float(similarities[idx])
                })
        
        return results

    def get_relevant_context(self, query: str, max_chars: int = 4000) -> str:
        """
        Obtient le contexte pertinent pour une requête donnée.
        
        Args:
            query: La requête de recherche
            max_chars: Le nombre maximum de caractères à retourner
            
        Returns:
            Un texte contenant les informations pertinentes des documents
        """
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        # Construire le contexte à partir des résultats
        context = "Informations juridiques pertinentes :\n\n"
        
        total_chars = len(context)
        for i, result in enumerate(results):
            doc_info = f"Document {i+1} ({os.path.basename(result['path'])}, score: {result['score']:.2f}):\n"
            doc_content = result['content']
            
            # Vérifier si l'ajout de ce document dépasserait la limite de caractères
            if total_chars + len(doc_info) + len(doc_content) + 2 > max_chars:
                # Tronquer le contenu pour respecter la limite
                available_chars = max_chars - total_chars - len(doc_info) - 2
                if available_chars > 100:  # S'assurer qu'il reste assez d'espace pour du contenu utile
                    doc_content = doc_content[:available_chars] + "..."
                else:
                    break
            
            context += doc_info + doc_content + "\n\n"
            total_chars = len(context)
            
            if total_chars >= max_chars:
                break
        
        return context
