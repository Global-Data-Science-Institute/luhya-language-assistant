
import React from 'react';

const MarkdownText = ({ text }) => {
  if (!text) return null;

  // Split text by ** patterns and render accordingly
  const parts = text.split(/(\*\*.*?\*\*)/g);
  
  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          // This is bold text
          const boldContent = part.slice(2, -2);
          return <strong key={index}>{boldContent}</strong>;
        }
        // Regular text
        return <span key={index}>{part}</span>;
      })}
    </>
  );
};

export default MarkdownText;