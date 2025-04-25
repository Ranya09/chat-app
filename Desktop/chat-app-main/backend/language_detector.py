def detect_language(text):
    """
    Détecte si le texte est en français ou en dialecte tunisien.
    
    Args:
        text (str): Le texte à analyser
        
    Returns:
        str: "french" ou "tunisian"
    """
    # Mots et expressions caractéristiques du dialecte tunisien
    tunisian_markers = [
        "chneya", "شنية", "kifech", "كيفاش", "3la", "على", "fi", "في", "enti", "انتي",
        "ena", "انا", "mte3", "متاع", "barcha", "برشا", "yezzi", "يزي", "tawa", "توا",
        "chkoun", "شكون", "waqteh", "وقتاه", "lahna", "لهنا", "fama", "فما", "mech", "مش",
        "bellehi", "بالهي", "ya3tik", "يعطيك", "sahbi", "صاحبي", "3andi", "عندي",
        "9oli", "قولي", "7aja", "حاجة", "barcha", "برشا", "3lech", "علاش", "chnowa", "شنوة",
        "bech", "باش", "ma3neha", "معناها", "khalini", "خليني", "na3ref", "نعرف",
        "lazem", "لازم", "mawjoud", "موجود", "9anoun", "قانون", "7a9", "حق", "chghol", "شغل"
    ]
    
    # Compteur pour les marqueurs tunisiens
    tunisian_count = 0
    
    # Convertir le texte en minuscules pour la comparaison
    lower_text = text.lower()
    
    # Vérifier la présence de marqueurs tunisiens
    for marker in tunisian_markers:
        if marker in lower_text:
            tunisian_count += 1
    
    # Si au moins 2 marqueurs tunisiens sont présents, considérer comme du tunisien
    if tunisian_count >= 2:
        return "tunisian"
    
    # Par défaut, considérer comme du français
    return "french"
