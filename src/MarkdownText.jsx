// MarkdownText.jsx - Simpler version
import React from 'react';

const MarkdownText = ({ text }) => {
  if (!text) return null;

  // Split and process the text
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          // Bold text
          const content = part.slice(2, -2);
          return <strong key={index}>{content}</strong>;
        } else if (part.startsWith('*') && part.endsWith('*')) {
          // Italic text
          const content = part.slice(1, -1);
          return <em key={index}>{content}</em>;
        }
        // Regular text
        return <span key={index}>{part}</span>;
      })}
    </>
  );
};

export default MarkdownText;