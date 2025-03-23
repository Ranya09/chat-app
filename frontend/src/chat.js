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

    setLoading(true);

    try {
      // Envoie de la requête à l'API FastAPI
      const res = await axios.post("http://127.0.0.1:8000/chat/", {
        message: message,
        role: "user",
        conversation_id: conversationId,
      });

      setResponse(res.data.response); // Affiche la réponse de l'API
    } catch (error) {
      console.error("Error during the API request", error);
      setResponse("There was an error with the request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1>Chat with AI</h1>
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
            <p>{response}</p>
          </>
        )}
      </div>
    </div>
  );
}

export default Chat;
