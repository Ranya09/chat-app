import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./ChatStyles.css";
import { FaMoon, FaSun, FaSearch, FaFileAlt, FaLanguage, FaStar, FaRegStar, FaFileDownload, FaThumbsUp, FaFileUpload } from "react-icons/fa";

function ImprovedChat() {
  const [message, setMessage] = useState("");
  const [conversationId] = useState("123");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [darkMode, setDarkMode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [filteredMessages, setFilteredMessages] = useState([]);
  const [currentLanguage, setCurrentLanguage] = useState("fr");
  const messagesEndRef = useRef(null);
  
  // États pour le système de feedback
  const [showFeedback, setShowFeedback] = useState(false);
  const [currentRating, setCurrentRating] = useState(0);
  const [feedbackComment, setFeedbackComment] = useState("");
  const [currentFeedbackMessageIndex, setCurrentFeedbackMessageIndex] = useState(null);
  
  // États pour l'upload de documents
  const [showDocumentUpload, setShowDocumentUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState(null);

  // Suggestions bilingues
  const suggestions = {
    fr: [
      "Quels sont mes droits en tant que salarié ?",
      "Comment créer une entreprise en Tunisie ?",
      "Procédure de divorce en Tunisie",
      "Lois sur la propriété immobilière",
      "Droits des consommateurs en Tunisie"
    ],
    ar: [
      "ما هي حقوقي كموظف؟",
      "كيفية إنشاء شركة في تونس؟",
      "إجراءات الطلاق في تونس",
      "قوانين الملكية العقارية",
      "حقوق المستهلك في تونس"
    ]
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  useEffect(() => {
    document.documentElement.setAttribute('dir', currentLanguage === "ar" ? 'rtl' : 'ltr');
    
    if (currentLanguage === "ar") {
      document.body.classList.add('rtl-layout');
    } else {
      document.body.classList.remove('rtl-layout');
    }
  }, [currentLanguage]);

  useEffect(() => {
    if (searchQuery.trim() === "") {
      setFilteredMessages(messages);
    } else {
      setFilteredMessages(messages.filter(msg => msg.content.toLowerCase().includes(searchQuery.toLowerCase())));
    }
  }, [searchQuery, messages]);

  // Fonction pour détecter la langue d'un texte
  const detectLanguage = (text) => {
    const arabicPattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+/;
    return arabicPattern.test(text) ? "ar" : "fr";
  };

  const toggleLanguage = () => {
    setCurrentLanguage(prev => prev === "fr" ? "ar" : "fr");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message.trim()) return;

    const detectedLanguage = detectLanguage(message);
    setCurrentLanguage(detectedLanguage);
    
    setMessages(prev => [...prev, { 
      role: "user", 
      content: message,
      language: detectedLanguage 
    }]);
    
    setMessage("");
    setLoading(true);
    setError(null);

    try {
      const res = await axios.post("http://127.0.0.1:8000/chat/", {
        message,
        role: "user",
        conversation_id: conversationId,
      }, {
        headers: { 'Content-Type': 'application/json' }
      });

      const responseLanguage = res.data.language === "arabic" ? "ar" : "fr";
      setCurrentLanguage(responseLanguage);

      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: res.data.response,
        language: responseLanguage
      }]);
    } catch (error) {
      setError(currentLanguage === "ar" 
        ? "حدث خطأ أثناء الاتصال بالخادم." 
        : "Une erreur s'est produite lors de la communication avec le serveur.");
      console.error("Error details:", error);
    } finally {
      setLoading(false);
    }
  };

  const exportConversation = () => {
    const conversationText = messages.map((msg) => {
      const sender = msg.role === "user" 
        ? (msg.language === "ar" ? "أنت" : "Vous") 
        : (msg.language === "ar" ? "المساعد" : "Assistant");
      return `${sender}: ${msg.content}`;
    }).join("\n\n");
    
    const blob = new Blob([conversationText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = currentLanguage === "ar" ? "محادثة-قانونية.txt" : "conversation-juridique.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const submitFeedback = async () => {
    if (currentRating === 0 || currentFeedbackMessageIndex === null) return;
    
    try {
      await axios.post("http://127.0.0.1:8000/feedback/", {
        conversation_id: conversationId,
        message_id: currentFeedbackMessageIndex.toString(),
        rating: currentRating,
        comment: feedbackComment
      });
      
      const updatedMessages = [...messages];
      updatedMessages[currentFeedbackMessageIndex] = {
        ...updatedMessages[currentFeedbackMessageIndex],
        rated: true
      };
      setMessages(updatedMessages);
      
      setShowFeedback(false);
      setCurrentRating(0);
      setFeedbackComment("");
      setCurrentFeedbackMessageIndex(null);
      
      alert(currentLanguage === "ar" 
        ? "شكرا على ملاحظاتك!" 
        : "Merci pour votre feedback !");
    } catch (error) {
      console.error("Erreur lors de l'envoi du feedback:", error);
    }
  };

  // Fonction pour gérer l'upload de document
  const handleFileUpload = async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('conversation_id', conversationId);
    formData.append('language', currentLanguage);

    try {
      setUploadStatus(currentLanguage === "ar" ? "جاري الرفع..." : "Upload en cours...");
      
      const res = await axios.post("http://127.0.0.1:8000/upload_document/", formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setUploadStatus(currentLanguage === "ar" 
        ? "تم رفع المستند بنجاح!" 
        : "Document uploadé avec succès!");
      
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: currentLanguage === "ar" 
          ? `تم تحليل المستند بنجاح:\n\n${res.data.summary}` 
          : `Document analysé avec succès:\n\n${res.data.summary}`,
        language: currentLanguage,
        isDocument: true,
        documentName: selectedFile.name
      }]);
      
      setShowDocumentUpload(false);
      setSelectedFile(null);
      setUploadProgress(0);
      setTimeout(() => setUploadStatus(null), 3000);
    } catch (error) {
      console.error("Erreur lors de l'upload:", error);
      setUploadStatus(currentLanguage === "ar" 
        ? "حدث خطأ أثناء رفع المستند" 
        : "Erreur lors de l'upload du document");
    }
  };

  const formatLegalText = (text, language) => {
    let formattedText = text;
    
    if (language === "ar") {
      formattedText = formattedText.replace(
        /(مادة|المادة|قانون|القانون|مرسوم|المرسوم|فصل|الفصل)\s+(\d+[-\d]*)/g,
        '<span class="legal-reference">$1 $2</span>'
      );
      
      formattedText = formattedText
        .replace(/^(\d+\.\s+)(.+)$/gm, '<h3>$1$2</h3>')
        .replace(/^(\*\s+)(.+)$/gm, '<div class="bullet-point">$1$2</div>')
        .replace(/^(أوصي.+)$/gm, '<div class="recommendation">$1</div>');
      
      return <div className="arabic-text" dangerouslySetInnerHTML={{ __html: formattedText }} />;
    } else {
      formattedText = formattedText.replace(
        /(article|Article|loi|Loi|décret|Décret|code|Code)\s+(\d+[-\d]*)/g,
        '<span class="legal-reference">$1 $2</span>'
      );
      
      formattedText = formattedText
        .replace(/^(\d+\.\s+)(.+)$/gm, '<h3>$1$2</h3>')
        .replace(/^(\*\s+)(.+)$/gm, '<div class="bullet-point">$1$2</div>')
        .replace(/^(Je vous recommande.+)$/gm, '<div class="recommendation">$1</div>');
      
      return <div dangerouslySetInnerHTML={{ __html: formattedText }} />;
    }
  };

  return (
    <div className={`chat-container ${currentLanguage === "ar" ? "rtl-container" : ""}`}>
      <div className="top-buttons">
        <button className="theme-toggle" onClick={() => setDarkMode(!darkMode)}>
          {darkMode ? <FaSun /> : <FaMoon />}
        </button>
        <button className="language-toggle" onClick={toggleLanguage}>
          <FaLanguage />
          <span>{currentLanguage === "ar" ? "Français" : "العربية"}</span>
        </button>
      </div>

      <div className="chat-header">
        <h1>{currentLanguage === "ar" ? "المساعد القانوني التونسي" : "Assistant Juridique Tunisien"}</h1>
        <p className="subtitle">
          {currentLanguage === "ar" 
            ? "يجيب على أسئلتك القانونية باللغتين العربية والفرنسية" 
            : "Répond à vos questions juridiques en français et en arabe"}
        </p>
      </div>

      {messages.length > 0 && (
        <div className="search-container">
          <input 
            type="text" 
            className={`search-input ${currentLanguage === "ar" ? "arabic-text" : ""}`}
            placeholder={currentLanguage === "ar" ? "بحث..." : "Rechercher..."}
            value={searchQuery} 
            onChange={(e) => setSearchQuery(e.target.value)}
            dir={currentLanguage === "ar" ? "rtl" : "ltr"}
          />
          <FaSearch className="search-icon" />
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className={`welcome-message ${currentLanguage === "ar" ? "arabic-text" : ""}`}>
            <h2>{currentLanguage === "ar" 
              ? "مرحبًا بك في المساعد القانوني التونسي" 
              : "Bienvenue sur l'Assistant Juridique Tunisien"}
            </h2>
            <p>
              {currentLanguage === "ar"
                ? "يمكنني مساعدتك في فهم القوانين واللوائح التونسية. اطرح سؤالًا حول القانون التونسي."
                : "Je peux vous aider à comprendre les lois et réglementations tunisiennes. Posez une question sur le droit tunisien."}
            </p>
            
            <div className="suggestions-container">
              <p className="suggestions-title">
                {currentLanguage === "ar" ? "اقتراحات الأسئلة:" : "Suggestions de questions :"}
              </p>
              <div className="suggestion-chips">
                {suggestions[currentLanguage].map((suggestion, index) => (
                  <div 
                    key={index} 
                    className={`suggestion-chip ${currentLanguage === "ar" ? "arabic-text" : ""}`}
                    onClick={() => setMessage(suggestion)}
                  >
                    {suggestion}
                  </div>
                ))}
              </div>
            </div>
            
            <button 
              className="document-button"
              onClick={() => setShowDocumentUpload(true)}
            >
              <FaFileUpload style={{ marginRight: currentLanguage === "ar" ? '0' : '5px', marginLeft: currentLanguage === "ar" ? '5px' : '0' }} />
              {currentLanguage === "ar" ? "رفع مستند قانوني" : "Uploader un document juridique"}
            </button>
          </div>
        ) : (
          (searchQuery.trim() === "" ? messages : filteredMessages).map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role}-message ${msg.isDocument ? 'document-message' : ''}`}
            >
              <div className={`message-header ${msg.language === "ar" ? "arabic-text" : ""}`}>
                {msg.role === "user" 
                  ? (msg.language === "ar" ? "أنت" : "Vous") 
                  : (msg.language === "ar" ? "المساعد" : "Assistant")}
                
                {msg.role === "assistant" && !msg.rated && !msg.isDocument && (
                  <button 
                    className="feedback-button"
                    onClick={() => {
                      setCurrentFeedbackMessageIndex(index);
                      setShowFeedback(true);
                    }}
                  >
                    <FaThumbsUp />
                    <span>{msg.language === "ar" ? "تقييم" : "Évaluer"}</span>
                  </button>
                )}
              </div>
              <div className="message-content">
                {msg.role === "assistant" 
                  ? (msg.isDocument 
                      ? <div className={`document-preview ${msg.language === "ar" ? "arabic-text" : ""}`}>
                          {formatLegalText(msg.content, msg.language)}
                          <button className="download-document-button">
                            <FaFileDownload />
                            <span>{msg.language === "ar" ? "تحميل المستند" : "Télécharger le document"}</span>
                          </button>
                        </div>
                      : formatLegalText(msg.content, msg.language))
                  : <div className={msg.language === "ar" ? "arabic-text" : ""}>{msg.content}</div>}
              </div>
            </div>
          ))
        )}
        {loading && (
          <div className="message assistant-message">
            <div className={`message-header ${currentLanguage === "ar" ? "arabic-text" : ""}`}>
              {currentLanguage === "ar" ? "المساعد" : "Assistant"}
            </div>
            <div className="message-content loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        {error && <div className={`error-message ${currentLanguage === "ar" ? "arabic-text" : ""}`}>{error}</div>}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="message-form">
        <textarea
          value={message}
          onChange={(e) => {
            setMessage(e.target.value);
            if (e.target.value) {
              setCurrentLanguage(detectLanguage(e.target.value));
            }
          }}
          placeholder={currentLanguage === "ar" ? "اطرح سؤالك القانوني هنا..." : "Posez votre question juridique ici..."}
          rows="3"
          disabled={loading}
          className={currentLanguage === "ar" ? "arabic-text" : ""}
          dir={currentLanguage === "ar" ? "rtl" : "ltr"}
        />
        <div className="button-container">
          {messages.length > 0 && (
            <button 
              type="button" 
              onClick={exportConversation} 
              className={`export-button ${currentLanguage === "ar" ? "arabic-text" : ""}`}
              disabled={loading}
            >
              <FaFileAlt style={{ marginRight: currentLanguage === "ar" ? '0' : '5px', marginLeft: currentLanguage === "ar" ? '5px' : '0' }} />
              {currentLanguage === "ar" ? "تصدير" : "Exporter"}
            </button>
          )}
          <button 
            type="button" 
            onClick={() => setShowDocumentUpload(true)} 
            className={`document-button ${currentLanguage === "ar" ? "arabic-text" : ""}`}
            disabled={loading}
          >
            <FaFileUpload style={{ marginRight: currentLanguage === "ar" ? '0' : '5px', marginLeft: currentLanguage === "ar" ? '5px' : '0' }} />
            {currentLanguage === "ar" ? "رفع مستند" : "Uploader un document"}
          </button>
          <button 
            type="submit" 
            disabled={loading || !message.trim()} 
            className={currentLanguage === "ar" ? "arabic-text" : ""}
          >
            {loading 
              ? (currentLanguage === "ar" ? "جاري الإرسال..." : "Envoi...") 
              : (currentLanguage === "ar" ? "إرسال" : "Envoyer")}
          </button>
        </div>
      </form>

      {/* Modal de feedback */}
      {showFeedback && (
        <>
          <div className="modal-overlay" onClick={() => setShowFeedback(false)}></div>
          <div className="feedback-modal">
            <h3 className={currentLanguage === "ar" ? "arabic-text" : ""}>
              {currentLanguage === "ar" ? "قيم هذه الإجابة" : "Évaluez cette réponse"}
            </h3>
            <div className="rating-stars">
              {[1, 2, 3, 4, 5].map((rating) => (
                <span 
                  key={rating}
                  className={`star ${currentRating >= rating ? "active" : ""}`}
                  onClick={() => setCurrentRating(rating)}
                >
                  {currentRating >= rating ? <FaStar /> : <FaRegStar />}
                </span>
              ))}
            </div>
            <textarea
              value={feedbackComment}
              onChange={(e) => setFeedbackComment(e.target.value)}
              placeholder={currentLanguage === "ar" ? "تعليقات إضافية (اختياري)" : "Commentaires additionnels (optionnel)"}
              rows="3"
              className={currentLanguage === "ar" ? "arabic-text" : ""}
              dir={currentLanguage === "ar" ? "rtl" : "ltr"}
            />
            <div className="feedback-buttons">
              <button 
                onClick={() => setShowFeedback(false)}
                className={currentLanguage === "ar" ? "arabic-text" : ""}
              >
                {currentLanguage === "ar" ? "إلغاء" : "Annuler"}
              </button>
              <button 
                onClick={submitFeedback}
                className={currentLanguage === "ar" ? "arabic-text" : ""}
                disabled={currentRating === 0}
              >
                {currentLanguage === "ar" ? "إرسال" : "Envoyer"}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Modal d'upload de document */}
      {showDocumentUpload && (
        <>
          <div className="modal-overlay" onClick={() => setShowDocumentUpload(false)}></div>
          <div className="document-modal">
            <h3 className={currentLanguage === "ar" ? "arabic-text" : ""}>
              {currentLanguage === "ar" ? "رفع مستند للتحليل" : "Uploader un document pour analyse"}
            </h3>
            
            <div className="file-upload-container">
              <input
                type="file"
                id="document-upload"
                accept=".pdf,.doc,.docx,.txt"
                onChange={(e) => setSelectedFile(e.target.files[0])}
                className="file-input"
              />
              <label htmlFor="document-upload" className="file-upload-label">
                {selectedFile 
                  ? selectedFile.name 
                  : (currentLanguage === "ar" 
                      ? "اختر ملف (PDF, DOC, TXT)" 
                      : "Choisir un fichier (PDF, DOC, TXT)")}
              </label>
              
              {selectedFile && (
                <div className="file-info">
                  <p>{currentLanguage === "ar" ? "حجم الملف:" : "Taille du fichier:"} {(selectedFile.size / 1024).toFixed(2)} KB</p>
                </div>
              )}
              
              {uploadProgress > 0 && (
                <div className="upload-progress">
                  <div 
                    className="progress-bar" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                  <span>{uploadProgress}%</span>
                </div>
              )}
              
              {uploadStatus && (
                <div className={`upload-status ${uploadStatus.includes("succès") || uploadStatus.includes("نجاح") ? "success" : "error"}`}>
                  {uploadStatus}
                </div>
              )}
            </div>
            
            <div className="document-buttons">
              <button 
                onClick={() => setShowDocumentUpload(false)}
                className={currentLanguage === "ar" ? "arabic-text" : ""}
              >
                {currentLanguage === "ar" ? "إلغاء" : "Annuler"}
              </button>
              <button 
                onClick={handleFileUpload}
                className={currentLanguage === "ar" ? "arabic-text" : ""}
                disabled={!selectedFile || uploadProgress > 0}
              >
                {currentLanguage === "ar" ? "رفع" : "Uploader"}
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default ImprovedChat;