import { useState } from 'react';
import PdfUpload from './components/PdfUpload';
import ChatInterface from './components/ChatInterface';

function App() {
  const [filename, setFilename] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);
  const [showChat, setShowChat] = useState(false);
  const [fadeOutUpload, setFadeOutUpload] = useState(false);
  const [hideUpload, setHideUpload] = useState(false);
  const [chatKey, setChatKey] = useState(0);
  const [fadeOutChat, setFadeOutChat] = useState(false);

  const handleUpload = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload/', {
        method: 'POST',
        body: formData,
      });

      const text = await response.text();
      if (!response.ok) throw new Error(text || 'Upload failed');

      const result = JSON.parse(text);
      console.log('✅ Upload success:', result);

      setFilename(result.filename);

      if (showChat) {
        setFadeOutChat(true);
        setTimeout(() => {
          setShowChat(false);
          setFadeOutChat(false);
          setShowSuccess(true);
          setTimeout(() => {
            setChatKey((prev) => prev + 1);
            setShowSuccess(false);
            setShowChat(true);
          }, 2000);
        }, 500);
        return;
      }

      setFadeOutUpload(true);
      setTimeout(() => {
        setHideUpload(true);
        setShowSuccess(true);
        setTimeout(() => {
          setShowSuccess(false);
          setShowChat(true);
        }, 2000);
      }, 500);
    } catch (err) {
      console.error('❌ Upload error:', err.message);
      alert(`❌ Upload failed: ${err.message}`);
    }
  };

  return (
    <div className="upload-wrapper">
      {!hideUpload && (
        <div className={`upload-box-wrapper ${fadeOutUpload ? 'fade-out' : ''}`}>
          {/* ✅ Title above upload box without altering layout */}
          <div style={{ marginBottom: '20px', textAlign: 'center' }}>
            <h1 style={{
              fontSize: '2rem',
              color: '#00ffcc',
              fontWeight: 'bold',
              textShadow: '0 0 10px rgba(0, 255, 204, 0.3)',
              margin: 0,
              padding: 0,
            }}>
              PDF-CHATBOT
            </h1>
          </div>
          <PdfUpload onUpload={handleUpload} />
        </div>
      )}

      {showSuccess && (
        <div className="success-message fade-in">
          ✅ Uploaded: {filename}
        </div>
      )}

      {showChat && (
        <div className={`chat-wrapper ${fadeOutChat ? 'fade-out' : 'fade-in'}`}>
          <div className="filename-header">
            ✅ Uploaded: {filename}
          </div>
          <ChatInterface key={chatKey} onUploadNewPdf={handleUpload} />
        </div>
      )}
    </div>
  );
}

export default App;
