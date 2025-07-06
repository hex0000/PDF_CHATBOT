import { useRef } from 'react';
import './PdfUpload.css'; // Link to our plain CSS

function PdfUpload({ onUpload }) {
  const fileInputRef = useRef(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    processFile(file);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    processFile(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const openFileDialog = () => {
    fileInputRef.current.click();
  };

  const processFile = (file) => {
    if (file && file.type === 'application/pdf') {
      onUpload(file); // App.jsx will handle success display
    } else {
      alert('Please upload a valid PDF file.');
    }
  };

  return (
    <div className="upload-wrapper">
      <div
        className="upload-box"
        onClick={openFileDialog}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
      >
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileSelect}
          ref={fileInputRef}
          className="hidden-input"
        />

        <div className="upload-content">
          <div className="upload-icon">📎</div>
          <p className="upload-text">Drop your PDF here</p>
          <p className="upload-subtext">or click to browse</p>
        </div>
      </div>
    </div>
  );
}

export default PdfUpload;
