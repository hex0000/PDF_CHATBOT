// src/components/GlassyBox.jsx

function GlassyBox({ children }) {
    return (
      <div
        style={{
          backdropFilter: 'blur(10px)',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          borderRadius: '20px',
          padding: '2rem',
          maxWidth: '800px',
          margin: '4rem auto',
          boxShadow: '0 8px 32px rgba(0,0,0,0.3)',
        }}
      >
        {children}
      </div>
    );
  }
  
  export default GlassyBox;
  