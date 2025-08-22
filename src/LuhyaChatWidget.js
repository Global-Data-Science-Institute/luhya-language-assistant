import React, { useState, useRef, useEffect } from 'react';

const LuhyaChatWidget = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Muraho! I\'m your Luhya language assistant. Ask me about translations, proverbs, or cultural insights!',
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      role: 'user',
      content: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputText,
          max_results: 5
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error connecting to the server. Please make sure the backend is running.',
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const MessageContent = ({ content }) => {
    return (
      <div 
        dangerouslySetInnerHTML={{ 
          __html: content.replace(/\n/g, '<br>') 
        }} 
      />
    );
  };

  const AIIcon = () => (
    <svg stroke="none" fill="black" strokeWidth="1.5" viewBox="0 0 24 24" aria-hidden="true" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z"></path>
    </svg>
  );

  const UserIcon = () => (
    <svg stroke="none" fill="black" strokeWidth="0" viewBox="0 0 16 16" height="20" width="20" xmlns="http://www.w3.org/2000/svg">
      <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4Zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10Z"></path>
    </svg>
  );

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Chat Button */}
      <button
        className="inline-flex items-center justify-center text-sm font-medium disabled:pointer-events-none disabled:opacity-50 border rounded-full w-16 h-16 bg-black hover:bg-gray-700 m-0 cursor-pointer border-gray-200 p-0 normal-case leading-5 hover:text-gray-900"
        type="button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          width="30" 
          height="40" 
          viewBox="0 0 24 24" 
          fill="none"
          stroke="currentColor" 
          strokeWidth="2" 
          strokeLinecap="round" 
          strokeLinejoin="round"
          className="text-white block border-gray-200 align-middle"
        >
          <path d="m3 21 1.9-5.7a8.5 8.5 0 1 1 3.8 3.8z" className="border-gray-200"></path>
        </svg>
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div 
          className="fixed bottom-[calc(4rem+1.5rem)] right-0 mr-4 bg-white p-6 rounded-lg border border-[#e5e7eb] w-[440px] h-[634px]"
          style={{ boxShadow: '0 0 #0000, 0 0 #0000, 0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
        >
          {/* Header */}
          <div className="flex flex-col space-y-1.5 pb-6">
            <h2 className="font-semibold text-lg tracking-tight">🌍 Luhya Language Assistant</h2>
            <p className="text-sm text-[#6b7280] leading-3">Preserving indigenous languages through AI</p>
          </div>

          {/* Chat Container */}
          <div className="pr-4 h-[474px] overflow-y-auto" style={{ minWidth: '100%', display: 'table' }}>
            {messages.map((message, index) => (
              <div key={index} className="flex gap-3 my-4 text-gray-600 text-sm flex-1">
                <span className="relative flex shrink-0 overflow-hidden rounded-full w-8 h-8">
                  <div className="rounded-full bg-gray-100 border p-1">
                    {message.role === 'assistant' ? <AIIcon /> : <UserIcon />}
                  </div>
                </span>
                <div className="leading-relaxed flex-1">
                  <span className="block font-bold text-gray-700">
                    {message.role === 'assistant' ? 'Luhya AI' : 'You'}
                  </span>
                  <div className="mt-1">
                    <MessageContent content={message.content} />
                  </div>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-2 text-xs text-gray-500">
                      Sources: {message.sources.map(s => s.metadata.type).join(', ')}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-3 my-4 text-gray-600 text-sm flex-1">
                <span className="relative flex shrink-0 overflow-hidden rounded-full w-8 h-8">
                  <div className="rounded-full bg-gray-100 border p-1">
                    <AIIcon />
                  </div>
                </span>
                <div className="leading-relaxed">
                  <span className="block font-bold text-gray-700">Luhya AI</span>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500"></div>
                    <span>Searching Luhya corpus...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="flex items-center pt-0">
            <div className="flex items-center justify-center w-full space-x-2">
              <input
                className="flex h-10 w-full rounded-md border border-[#e5e7eb] px-3 py-2 text-sm placeholder-[#6b7280] focus:outline-none focus:ring-2 focus:ring-[#9ca3af] disabled:cursor-not-allowed disabled:opacity-50 text-[#030712] focus-visible:ring-offset-2"
                placeholder="Ask about Luhya words, proverbs, or culture..."
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <button
                className="inline-flex items-center justify-center rounded-md text-sm font-medium text-[#f9fafb] disabled:pointer-events-none disabled:opacity-50 bg-black hover:bg-[#111827E6] h-10 px-4 py-2"
                onClick={handleSendMessage}
                disabled={isLoading || !inputText.trim()}
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LuhyaChatWidget;