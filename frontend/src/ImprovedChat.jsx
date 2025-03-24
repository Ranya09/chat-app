import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./ChatStyles.css";

function ImprovedChat() {
  const [message, setMessage] = useState("");
  const [conversationId] = useState("123"); // ID statique pour simplifier
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  // Fonction pour faire défiler automatiquement vers le bas
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message.trim()) return;

    // Ajouter le message de l'utilisateur à l'historique
    setMessages((prevMessages) => [
      ...prevMessages,
      { role: "user", content: message },
    ]);
    
    const userMessage = message;
    setMessage(""); // Vider le champ de saisie
    setLoading(true);
    setError(null);

    try {
      // Préparation des données à envoyer
      const requestData = {
        message: userMessage,
        role: "user",
        conversation_id: conversationId,
      };
      
      console.log("Envoi de la requête avec les données:", requestData);
      
      // Envoie de la requête à l'API FastAPI
      const res = await axios.post("http://127.0.0.1:8000/chat/", requestData, {
        headers: {
          'Content-Type': 'application/json',
        }
      }) ;

      console.log("Réponse reçue:", res.data);

      // Ajouter la réponse de l'assistant à l'historique
      setMessages((prevMessages) => [
        ...prevMessages,
        { role: "assistant", content: res.data.response },
      ]);
    } catch (error) {
      console.error("Erreur lors de la requête API:", error);
      
      // Afficher des informations détaillées sur l'erreur
      if (error.response) {
        // La requête a été faite et le serveur a répondu avec un code d'état
        console.error("Données d'erreur:", error.response.data);
        console.error("Statut d'erreur:", error.response.status);
        console.error("En-têtes d'erreur:", error.response.headers);
        
        setError(`Erreur ${error.response.status}: ${error.response.data.detail || "Une erreur s'est produite"}`);
      } else if (error.request) {
        // La requête a été faite mais aucune réponse n'a été reçue
        console.error("Requête sans réponse:", error.request);
        setError("Aucune réponse du serveur. Vérifiez que le serveur est en cours d'exécution.");
      } else {
        // Une erreur s'est produite lors de la configuration de la requête
        console.error("Erreur de configuration:", error.message);
        setError(`Erreur: ${error.message}`);
      }
      
      // Ajouter un message d'erreur à l'historique
      setMessages((prevMessages) => [
        ...prevMessages,
        { 
          role: "system", 
          content: "Une erreur s'est produite lors de la communication avec le serveur. Veuillez réessayer." 
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour extraire les sources juridiques des réponses
  const extractSources = (text) => {
    // Recherche des mentions de documents dans le texte
    const sourceRegex = /Document \d+\s*\(([^,]+),\s*score: [\d.]+\)/g;
    const matches = [...text.matchAll(sourceRegex)];
    
    if (matches.length === 0) return null;
    
    return (
      <div className="sources">
        <p className="sources-title">Sources juridiques :</p>
        <ul>
          {matches.map((match, index) => (
            <li key={index}>{match[1]}</li>
          ))}
        </ul>
      </div>
    );
  };

  // Fonction pour formater le texte avec mise en évidence des articles de loi
  const formatLegalText = (text) => {
    // Mise en évidence des références aux articles de loi
    const formattedText = text.replace(
      /(article|Article|loi|Loi|décret|Décret)\s+(\d+[-\d]*)/g,
      '<span class="legal-reference">$1 $2</span>'
    );
    
    return <div dangerouslySetInnerHTML={{ __html: formattedText }} />;
  };

  // Fonction pour exporter la conversation
  const exportConversation = () => {
    const conversationText = messages
      .map((msg) => `${msg.role === "user" ? "Vous" : msg.role === "assistant" ? "Assistant" : "Système"}: ${msg.content}`)
      .join("\n\n");
    
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

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Assistant Juridique Tunisien</h1>
        <p className="subtitle">Posez vos questions sur le droit tunisien</p>
      </div>

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h2>Bienvenue dans votre assistant juridique tunisien</h2>
            <p>
              Je peux vous aider à comprendre les lois et réglementations tunisiennes.
              Posez-moi une question sur le droit tunisien.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${
                msg.role === "user" 
                  ? "user-message" 
                  : msg.role === "assistant" 
                    ? "assistant-message" 
                    : "system-message"
              }`}
            >
              <div className="message-header">
                {msg.role === "user" 
                  ? "Vous" 
                  : msg.role === "assistant" 
                    ? "Assistant Juridique" 
                    : "Système"}
              </div>
              <div className="message-content">
                {msg.role === "assistant" 
                  ? formatLegalText(msg.content) 
                  : msg.content}
                {msg.role === "assistant" && extractSources(msg.content)}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant-message">
            <div className="message-header">Assistant Juridique</div>
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        {error && <div className="error-message">{error}</div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="message-form">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Posez votre question juridique ici..."
          rows="3"
          disabled={loading}
        />
        <div className="button-container">
          {messages.length > 0 && (
            <button 
              type="button" 
              onClick={exportConversation} 
              className="export-button"
              disabled={loading}
            >
              Exporter la conversation
            </button>
          )}
          <button type="submit" disabled={loading || !message.trim()}>
            {loading ? "Envoi..." : "Envoyer"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ImprovedChat;
