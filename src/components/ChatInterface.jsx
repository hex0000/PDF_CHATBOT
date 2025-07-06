import { useState, useRef } from 'react';

function ChatInterface({ filename, onUploadNewPdf }) {
  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) throw new Error('Server error.');

      const data = await response.json();
      setChatHistory((prev) => [...prev, { question, answer: data.answer }]);
      setQuestion('');
    } catch (err) {
      console.error('Fetch error:', err);
      alert('❌ Failed to fetch answer.');
    } finally {
      setLoading(false);
    }
  };

  const handleIconClick = () => {
    fileInputRef.current.click();
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      onUploadNewPdf(file); // ✅ trigger full PDF upload/reset
    } else {
      alert('❌ Please select a valid PDF file.');
    }
  };

  return (
    <div className="chat-glass-container">
      {/* Uploaded Filename */}
      {filename && (
        <div className="filename-header">
          📄 <span>{filename}</span>
        </div>
      )}

      {/* Chat History */}
      <div className="chat-history">
        {chatHistory.map((chat, idx) => (
          <div key={idx} className="chat-message">
            <p className="user-question">You: {chat.question}</p>
            <p className="ai-answer">AI: {chat.answer}</p>
          </div>
        ))}
      </div>

      {/* Chat Form */}
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          className="chat-input"
          placeholder="Ask your question..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />

        <button type="submit" className="chat-button" disabled={loading}>
          {loading ? 'Asking...' : 'Ask'}
        </button>

        <button
          type="button"
          className="chat-button"
          onClick={handleIconClick}
          title="Upload PDF"
          style={{ padding: '10px 14px', fontSize: '18px' }}
        >
          📎
        </button>

        <input
          type="file"
          ref={fileInputRef}
          accept="application/pdf"
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </form>
    </div>
  );
}

export default ChatInterface;
