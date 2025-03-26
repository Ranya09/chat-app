import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./ChatStyles.css";
import { FaMoon, FaSun, FaSearch, FaFileAlt, FaLanguage } from "react-icons/fa";
import translations from "./translations";

function ImprovedChat() {
  const [message, setMessage] = useState("");
  const [conversationId] = useState("123");
  // Toujours démarrer avec une nouvelle conversation contenant uniquement le message de bienvenue
  const [messages, setMessages] = useState([
    { 
      role: "assistant", 
      content: "Ahla bik! 👋 أهلا بيك في المستشار القانوني التونسي. كيفاش نجم نعاونك اليوم؟\n\nBienvenue dans l'Assistant Juridique Tunisien. Comment puis-je vous aider aujourd'hui?" 
    }
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [language, setLanguage] = useState("auto"); // "french", "tunisian" ou "auto"
  const messagesEndRef = useRef(null);
  
  // Fonction de traduction
  const t = (text) => translations[text] || text;

  const suggestions = [
    t("Quels sont mes droits en tant que salarié ?"),
    t("Comment créer une entreprise en Tunisie ?"),
    t("Procédure de divorce en Tunisie"),
    t("Lois sur la propriété immobilière"),
    t("Droits des consommateurs en Tunisie")
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  // Suppression de l'effet qui sauvegarde les messages dans le localStorage
  // pour ne pas conserver l'historique entre les sessions

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message.trim()) return;

    const userMessage = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setMessage("");
    setLoading(true);
    setError(null);

    try {
      // Ajouter un log pour déboguer
      console.log("Envoi de la requête au backend avec la langue:", language);
      
      const res = await axios.post("http://127.0.0.1:8000/chat/", {
        message: userMessage.content,
        role: "user",
        conversation_id: conversationId,
        language: language // Utiliser la langue sélectionnée par l'utilisateur
      }, {
        headers: { 'Content-Type': 'application/json' }
      });
      
      // Ajouter un log pour voir la réponse brute du backend
      console.log("Réponse brute du backend:", res.data.response);
      
      const botMessage = { role: "assistant", content: res.data.response };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setError(t("Une erreur s'est produite lors de la communication avec le serveur."));
      console.error("Erreur API:", error);
    } finally {
      setLoading(false);
    }
  };

  const exportConversation = () => {
    const conversationText = messages.map(msg => `${msg.role === "user" ? t("Vous") : t("Assistant")}: ${msg.content}`).join("\n\n");
    const blob = new Blob([conversationText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "conversation-juridique.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatLegalText = (text) => {
    // Créer un élément DOM temporaire pour manipuler le HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = text;
    
    // Extraire tous les liens existants et les remplacer par des marqueurs uniques
    const links = [];
    const linkElements = tempDiv.querySelectorAll('a');
    linkElements.forEach((link, index) => {
      const marker = `__LINK_MARKER_${index}__`;
      links.push({
        marker: marker,
        outerHTML: link.outerHTML
      });
      link.outerHTML = marker;
    });
    
    // Obtenir le texte sans les liens
    let formattedText = tempDiv.innerHTML;
    
    // Mise en évidence des références aux articles de loi (version tunisienne)
    formattedText = formattedText.replace(
      /(فصل|قانون|أمر|مرسوم)\s+(\d+[-\d]*)/g,
      '<span class="legal-reference">$1 $2</span>'
    );
    
    // Mise en évidence des références aux articles de loi (version française)
    formattedText = formattedText.replace(
      /(article|Article|loi|Loi|décret|Décret)\s+(\d+[-\d]*)/g,
      '<span class="legal-reference">$1 $2</span>'
    );
    
    // Mise en forme des titres et sections
    formattedText = formattedText
      // Formatage des titres numérotés (1., 2., etc.)
      .replace(/^(\d+\.\s+)(.+)$/gm, '<h3>$1$2</h3>')
      // Formatage des puces
      .replace(/^(\*\s+)(.+)$/gm, '<div class="bullet-point">$1$2</div>')
      // Formatage des recommandations (version tunisienne)
      .replace(/^(نوصيك.+)$/gm, '<div class="recommendation">$1</div>')
      // Formatage des recommandations (version française)
      .replace(/^(Je vous recommande.+)$/gm, '<div class="recommendation">$1</div>');
    
    // Réinsérer les liens originaux
    links.forEach(link => {
      formattedText = formattedText.replace(link.marker, link.outerHTML);
    });
    
    return <div dangerouslySetInnerHTML={{ __html: formattedText }} />;
  };

  // Fonction pour changer la langue
  const changeLanguage = (newLanguage) => {
    setLanguage(newLanguage);
  };

  // Fonction pour démarrer une nouvelle conversation
  const startNewConversation = () => {
    setMessages([
      { 
        role: "assistant", 
        content: "Ahla bik! 👋 أهلا بيك في المستشار القانوني التونسي. كيفاش نجم نعاونك اليوم؟\n\nBienvenue dans l'Assistant Juridique Tunisien. Comment puis-je vous aider aujourd'hui?" 
      }
    ]);
    setSearchQuery("");
    setError(null);
  };

  return (
    <div className="chat-container">
      <div className="top-controls">
        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </button>
        <div className="language-selector">
          <FaLanguage className="language-icon" />
          <select 
            value={language} 
            onChange={(e) => changeLanguage(e.target.value)}
            className="language-select"
          >
            <option value="auto">{t("Détection automatique")}</option>
            <option value="tunisian">{t("Dialecte tunisien")}</option>
            <option value="french">{t("Français")}</option>
          </select>
        </div>
      </div>
      <div className="chat-header">
        <h1>{t("Assistant Juridique Tunisien")}</h1>
        <button className="new-conversation-button" onClick={startNewConversation}>
          {t("Nouvelle conversation")}
        </button>
      </div>

      {messages.length > 0 && (
        <div className="search-container">
          <input type="text" className="search-input" placeholder={t("Rechercher...")} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} />
          <FaSearch className="search-icon" />
        </div>
      )}

      <div className="messages-container">
        {messages.filter(msg => msg.content.toLowerCase().includes(searchQuery.toLowerCase())).map((msg, index) => (
          <div key={index} className={`message ${msg.role}-message`}>
            <div className="message-header">{msg.role === "user" ? t("Vous") : t("Assistant")}</div>
            <div className="message-content">
              {msg.role === "assistant" ? formatLegalText(msg.content) : msg.content}
            </div>
          </div>
        ))}
        {loading && <div className="loading">{t("Envoi en cours...")}</div>}
        {error && <div className="error-message">{error}</div>}
        <div ref={messagesEndRef} />
      </div>

      <div className="suggestions-container">
        {suggestions.map((suggestion, index) => (
          <div key={index} className="suggestion-chip" onClick={() => setMessage(suggestion)}>
            {suggestion}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="message-form">
        <textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder={t("Posez votre question...")} rows="3" disabled={loading} />
        <div className="button-container">
          {messages.length > 0 && (
            <button type="button" onClick={exportConversation} className="export-button">
              <FaFileAlt style={{ marginRight: '5px' }} /> {t("Exporter")}
            </button>
          )}
          <button type="submit" disabled={loading || !message.trim()}>{t("Envoyer")}</button>
        </div>
      </form>
    </div>
  );
}

export default ImprovedChat;
