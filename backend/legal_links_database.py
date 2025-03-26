"""
Base de données de liens juridiques tunisiens pour enrichir les réponses du chatbot
"""

# Dictionnaire des liens vers les codes et lois tunisiens
LEGAL_LINKS = {
    # Codes principaux
    "code du travail": "https://legislation-securite.tn/fr/law/43968",
    "code des obligations et des contrats": "https://legislation-securite.tn/fr/law/41761",
    "code de commerce": "https://legislation-securite.tn/fr/law/44156",
    "code des sociétés commerciales": "https://legislation-securite.tn/fr/law/41782",
    "code pénal": "https://legislation-securite.tn/fr/law/44027",
    "code de procédure pénale": "https://legislation-securite.tn/fr/law/44029",
    "code de procédure civile": "https://legislation-securite.tn/fr/law/44028",
    "code des droits réels": "https://legislation-securite.tn/fr/law/41762",
    "code du statut personnel": "https://legislation-securite.tn/fr/law/41760",
    
    # Lois spécifiques
    "loi n° 83-112": "https://legislation-securite.tn/fr/law/41741",
    "décret n° 97-83": "https://legislation-securite.tn/fr/node/44474",
    
    # Institutions juridiques
    "tribunal administratif": "http://www.ta.gov.tn/",
    "cour de cassation": "http://www.e-justice.tn/",
    "ministère de la justice": "http://www.e-justice.tn/",
    "journal officiel": "http://www.iort.gov.tn/",
    
    # Ressources juridiques
    "législation tunisienne": "https://legislation-securite.tn/fr",
    "portail juridique tunisien": "https://www.jurisitetunisie.com/",
    "droit tunisien": "https://www.droitunisien.com/"
}

# Dictionnaire des liens vers des articles spécifiques
ARTICLE_LINKS = {
    # Code du travail
    "article 1 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-1",
    "article 2 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-2",
    "article 3 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-3",
    "article 4 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-4",
    "article 5 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-5",
    "article 6 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-6",
    "article 7 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-7",
    "article 8 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-8",
    "article 9 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-9",
    "article 10 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-10",
    "article 11 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-11",
    "article 12 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-12",
    "article 13 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-13",
    "article 14 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-14",
    "article 15 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-15",
    "article 20 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-20",
    "article 21 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-21",
    "article 22 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-22",
    "article 23 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-23",
    "article 24 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-24",
    "article 25 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-25",
    "article 30 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-30",
    "article 31 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-31",
    "article 32 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-32",
    "article 33 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-33",
    "article 34 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-34",
    "article 35 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-35",
    "article 40 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-40",
    "article 41 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-41",
    "article 42 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-42",
    "article 50 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-50",
    "article 52 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-52",
    "article 53 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-53",
    "article 54 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-54",
    "article 55 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-55",
    "article 60 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-60",
    "article 61 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-61",
    "article 62 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-62",
    "article 63 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-63",
    "article 64 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-64",
    "article 65 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-65",
    "article 66 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-66",
    "article 67 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-67",
    "article 68 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-68",
    "article 69 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-69",
    "article 70 du code du travail": "https://legislation-securite.tn/fr/law/43968#article-70",
    
    # Loi n° 83-112
    "article 1 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-1",
    "article 2 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-2",
    "article 3 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-3",
    "article 4 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-4",
    "article 5 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-5",
    "article 10 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-10",
    "article 15 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-15",
    "article 20 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-20",
    "article 25 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-25",
    "article 30 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-30",
    "article 33 de la loi n° 83-112": "https://legislation-securite.tn/fr/law/41741#article-33",
    
    # Décret n° 97-83
    "article 33 du décret n° 97-83": "https://legislation-securite.tn/fr/node/44474#article-33",
}

# Dictionnaire des liens vers des ressources juridiques spécifiques
RESOURCE_LINKS = {
    "droits des salariés": "https://www.jurisitetunisie.com/droit-du-travail/droits-des-salaries/",
    "création d'entreprise": "https://www.tunisieindustrie.gov.tn/fr/creation_entreprise.asp",
    "procédure de divorce": "https://www.jurisitetunisie.com/droit-de-la-famille/divorce/",
    "propriété immobilière": "https://www.jurisitetunisie.com/droit-immobilier/",
    "droits des consommateurs": "https://www.commerce.gov.tn/fr/protection-du-consommateur",
    "syndicats": "http://www.ugtt.org.tn/",
    "sécurité sociale": "http://www.cnss.tn/",
    "impôts": "http://www.impots.finances.gov.tn/",
    "douanes": "https://www.douane.gov.tn/",
    "registre de commerce": "https://www.registre-commerce.tn/"
}

def enrich_text_with_links(text):
    """
    Enrichit le texte avec des liens vers des ressources juridiques.
    
    Args:
        text (str): Le texte à enrichir
        
    Returns:
        str: Le texte enrichi avec des liens HTML
    """
    # Copie du texte original
    enriched_text = text
    
    # Enrichir avec des liens vers des articles spécifiques
    for article, link in ARTICLE_LINKS.items():
        # Recherche insensible à la casse
        pattern = article
        replacement = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{article}</a>'
        # Remplacer uniquement les occurrences complètes (pas les sous-chaînes)
        enriched_text = enriched_text.replace(pattern, replacement)
    
    # Enrichir avec des liens vers des codes et lois
    for code, link in LEGAL_LINKS.items():
        # Recherche insensible à la casse
        pattern = code
        replacement = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{code}</a>'
        # Remplacer uniquement les occurrences complètes (pas les sous-chaînes)
        enriched_text = enriched_text.replace(pattern, replacement)
    
    # Enrichir avec des liens vers des ressources spécifiques
    for resource, link in RESOURCE_LINKS.items():
        # Recherche insensible à la casse
        pattern = resource
        replacement = f'<a href="{link}" target="_blank" rel="noopener noreferrer">{resource}</a>'
        # Remplacer uniquement les occurrences complètes (pas les sous-chaînes)
        enriched_text = enriched_text.replace(pattern, replacement)
    
    return enriched_text
