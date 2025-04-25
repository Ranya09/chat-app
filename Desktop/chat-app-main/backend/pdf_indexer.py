import os
import glob
from typing import List, Dict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber

class PDFIndexer:
    def __init__(self, pdf_directory: str, index_file: str = "indexed_files.txt"):
        self.pdf_directory = pdf_directory
        self.index_file = index_file
        self.documents = []
        self.document_paths = []
        self.vectorizer = None
        self.document_vectors = None
        self.indexed_files = self.load_indexed_files()

    def load_indexed_files(self) -> set:
        if os.path.exists(self.index_file):
            with open(self.index_file, "r") as file:
                return set(line.strip() for line in file.readlines())
        return set()

    def save_indexed_file(self, pdf_path: str) -> None:
        with open(self.index_file, "a") as file:
            file.write(pdf_path + "\n")

    def extract_text_and_tables(self, file_path: str) -> str:
        full_text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    full_text += page_text + "\n"

                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = self.summarize_table_as_paragraph(table)
                            full_text += "\n[EXTRAIT DU TABLEAU]\n" + table_text + "\n"
        except Exception as e:
            print(f"Erreur lors de l'extraction du PDF : {e}")
        return full_text

    def summarize_table_as_paragraph(self, table: List[List[str]]) -> str:
        if not table or len(table) < 2:
            return "Le tableau est vide ou mal structuré."
        headers = table[0]
        rows = table[1:]
        paragraph = f"Ce tableau contient {len(rows)} lignes avec les colonnes suivantes : {', '.join(headers)}. "
        paragraph += "Exemples de données : "
        for row in rows[:min(3, len(rows))]:
            elements = [f"{headers[i]} : {row[i]}" for i in range(len(headers)) if i < len(row)]
            paragraph += "[" + ", ".join(elements) + "]. "
        return paragraph.strip()

    def index_documents(self) -> None:
        pdf_files = glob.glob(os.path.join(self.pdf_directory, "*.pdf"))
        if not pdf_files:
            print(f"Aucun fichier PDF trouvé dans {self.pdf_directory}")
            return

        for pdf_path in pdf_files:
            if pdf_path not in self.indexed_files:
                text = self.extract_text_and_tables(pdf_path)
                if text:
                    self.documents.append(text)
                    self.document_paths.append(pdf_path)
                    self.save_indexed_file(pdf_path)
                    print(f"Indexé: {os.path.basename(pdf_path)}")

        if self.documents:
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
                stop_words=french_stopwords,
                max_df=0.85,
                min_df=2
            )
            self.document_vectors = self.vectorizer.fit_transform(self.documents)
            print(f"Indexation terminée. {len(self.documents)} documents indexés.")
        else:
            print("Aucun document n'a pu être indexé.")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        if not self.vectorizer or self.document_vectors is None or len(self.documents) == 0:
            print("L'index n'a pas été créé. Veuillez d'abord indexer les documents.")
            return []

        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.document_vectors).flatten()
        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.0:
                results.append({
                    "path": self.document_paths[idx],
                    "content": self.documents[idx][:1000] + "...",
                    "score": float(similarities[idx])
                })
        return results

    def get_relevant_context(self, query: str, max_chars: int = 4000) -> str:
        results = self.search(query, top_k=3)
        if not results:
            return ""

        context = "Informations juridiques pertinentes :\n\n"
        total_chars = len(context)
        for i, result in enumerate(results):
            doc_info = f"Document {i+1} ({os.path.basename(result['path'])}, score: {result['score']:.2f}):\n"
            doc_content = result['content']
            if total_chars + len(doc_info) + len(doc_content) + 2 > max_chars:
                available_chars = max_chars - total_chars - len(doc_info) - 2
                if available_chars > 100:
                    doc_content = doc_content[:available_chars] + "..."
                else:
                    break
            context += doc_info + doc_content + "\n\n"
            total_chars = len(context)
            if total_chars >= max_chars:
                break
        return context
