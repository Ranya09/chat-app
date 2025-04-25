import React, { useState } from "react";
import axios from "axios";

function Chat() {
  const [message, setMessage] = useState("");
  const [conversationId] = useState("123"); // ID statique pour simplifier
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message) return;

    // Effacer la réponse précédente avant d'en demander une nouvelle
    setResponse("");
    setLoading(true);

    try {
      // Envoie de la requête à l'API FastAPI
      const res = await axios.post("http://127.0.0.1:8000/chat/", {
        message: message,
        role: "user",
        conversation_id: conversationId,
        language: "auto" // Utiliser la détection automatique de langue
      });

      setResponse(res.data.response); // Affiche la réponse de l'API
      console.log("Réponse brute du backend:", res.data.response); // Log pour déboguer
    } catch (error) {
      console.error("Error during the API request", error);
      setResponse("There was an error with the request.");
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour démarrer une nouvelle conversation
  const startNewConversation = () => {
    setResponse("");
    setMessage("");
  };

  return (
    <div>
      <h1>Chat with AI</h1>
      <button onClick={startNewConversation} style={{ marginBottom: '10px' }}>
        New Conversation
      </button>
      <form onSubmit={handleSubmit}>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type your message here"
          rows="4"
          cols="50"
        />
        <br />
        <button type="submit" disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </form>

      <div>
        {response && (
          <>
            <h2>AI Response:</h2>
            <div dangerouslySetInnerHTML={{ __html: response }} />
          </>
        )}
      </div>
    </div>
  );
}

export default Chat;
