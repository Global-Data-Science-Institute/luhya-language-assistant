import React, { useState, useRef, useEffect } from 'react';
import { 
  MessageCircle, 
  Settings, 
  History, 
  BookOpen, 
  Globe, 
  Menu,
  Send,
  User,
  Bot,
  Copy,
  MoreVertical,
  PlusCircle,
  Search,
  Zap
} from 'lucide-react';

const LuhyaRAGChat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'mulembe! I\'m your Luhya language assistant powered by TF-IDF search. I can help you with translations, word meanings, and cultural insights from our comprehensive Luhya database. What would you like to explore today?',
      timestamp: new Date(),
      sources: []
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState('current');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState({ status: 'connecting', cost: '$0.00' });
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check system health on mount
  useEffect(() => {
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const response = await fetch('https://luhya-language-assistant.vercel.app/api/health');
      if (response.ok) {
        const data = await response.json();
        setSystemStatus({ status: 'connected', cost: data.cost || '$0.00' });
      }
    } catch (error) {
      setSystemStatus({ status: 'error', cost: '$0.00' });
    }
  };

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputText,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
    const response = await fetch('https://luhya-language-assistant.vercel.app/api/chat', {
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
        id: Date.now() + 1,
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources || []
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const fallbackResponse = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'I apologize, but I\'m experiencing connectivity issues. The TF-IDF search system might be initializing. Please try again in a moment!',
        timestamp: new Date(),
        sources: []
      };
      
      setMessages(prev => [...prev, fallbackResponse]);
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

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const newConversation = () => {
    setMessages([
      {
        id: Date.now(),
        role: 'assistant',
        content: 'mulembe! I\'m your Luhya language assistant powered by TF-IDF search. I can help you with translations, word meanings, and cultural insights from our comprehensive Luhya database. What would you like to explore today?',
        timestamp: new Date(),
        sources: []
      }
    ]);
  };

  // Sample queries for quick testing
  const sampleQueries = [
    "How do you say good morning' in Luhya?",
    "What does mulembe mean?",
    "How do you say thank you in different Luhya dialects?",
    "What is the Luhya word for 'water'?",
    "Tell me about Luhya greetings"
  ];

  const getStatusColor = () => {
    switch (systemStatus.status) {
      case 'connected': return 'bg-green-500';
      case 'connecting': return 'bg-yellow-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (systemStatus.status) {
      case 'connected': return 'TF-IDF Ready';
      case 'connecting': return 'Initializing...';
      case 'error': return 'Connection Error';
      default: return 'Unknown';
    }
  };

  return (
    <div className="flex h-screen bg-gray-900">
      {/* Sidebar */}
      <div className={`bg-gray-900 text-white transition-all duration-300 ${sidebarCollapsed ? 'w-16' : 'w-80'} flex flex-col`}>
          {/* Header */}
          <div className="p-4 border-b border-gray-700">
            <div className="flex items-center justify-between">
              {!sidebarCollapsed && (
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                    <Zap className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h1 className="font-semibold text-lg">LuhyaAI</h1>
                    <p className="text-xs text-gray-400">TF-IDF Powered</p>
                  </div>
                </div>
              )}
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Menu className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* System Status */}
          {!sidebarCollapsed && (
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center space-x-2 text-sm">
                <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
                <span className="text-gray-300">{getStatusText()}</span>
                <span className="text-green-400 font-mono">{systemStatus.cost}</span>
              </div>
            </div>
          )}

          {/* New Chat Button */}
          <div className="p-4">
            <button 
              onClick={newConversation}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
            >
              <PlusCircle className="w-5 h-5" />
              {!sidebarCollapsed && <span>New Chat</span>}
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4">
            <div className="space-y-2">
              <div className={`flex items-center space-x-3 py-3 px-3 rounded-lg bg-gray-800 text-white`}>
                <MessageCircle className="w-5 h-5" />
                {!sidebarCollapsed && <span>Chat</span>}
              </div>
              <div className="flex items-center space-x-3 py-3 px-3 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                <BookOpen className="w-5 h-5" />
                {!sidebarCollapsed && <span>Dictionary</span>}
              </div>
              <div className="flex items-center space-x-3 py-3 px-3 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                <History className="w-5 h-5" />
                {!sidebarCollapsed && <span>History</span>}
              </div>
              <div className="flex items-center space-x-3 py-3 px-3 rounded-lg hover:bg-gray-800 cursor-pointer transition-colors">
                <Settings className="w-5 h-5" />
                {!sidebarCollapsed && <span>Settings</span>}
              </div>
            </div>

            {/* Sample Queries */}
            {!sidebarCollapsed && (
              <div className="mt-8">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Try asking:</h3>
                <div className="space-y-2">
                  {sampleQueries.slice(0, 3).map((query, idx) => (
                    <button
                      key={idx}
                      onClick={() => setInputText(query)}
                      className="w-full text-left p-2 text-xs text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
                    >
                      "{query}"
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Feature Info */}
            {!sidebarCollapsed && (
              <div className="mt-8">
                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Features</h3>
                <div className="space-y-1 text-xs text-gray-500">
                  <div className="flex items-center space-x-2">
                    <Zap className="w-3 h-3" />
                    <span>TF-IDF Search</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Globe className="w-3 h-3" />
                    <span>Multi-Dialect</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Bot className="w-3 h-3" />
                    <span>Zero Cost</span>
                  </div>
                </div>
              </div>
            )}
          </nav>

          {/* User Profile */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
              {!sidebarCollapsed && (
                <div className="flex-1">
                  <div className="font-medium text-sm">User</div>
                  <div className="text-xs text-gray-400">Free Access</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex-1 p-4 bg-gray-900">
          <div className="h-full bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden">
          {/* Chat Header */}
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900">Luhya Language Assistant</h2>
                <p className="text-sm text-gray-500">Powered by TF-IDF • {messages.length - 1} messages • Zero cost</p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1 text-xs text-gray-500">
                  <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
                  <span>{getStatusText()}</span>
                </div>
                <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                  <MoreVertical className="w-5 h-5 text-gray-500" />
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
            {messages.map((message) => (
              <div key={message.id} className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : ''}`}>
                {message.role === 'assistant' && (
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}
                
                <div className={`max-w-3xl ${message.role === 'user' ? 'order-first' : ''}`}>
                  <div className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user' 
                      ? 'bg-green-500 text-white ml-auto' 
                      : 'bg-white border border-gray-200'
                  }`}>
                    <div className="text-sm leading-relaxed whitespace-pre-wrap">
                    <MarkdownText text={message.content} />
                    </div>
                    
                    {message.sources && message.sources.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="text-xs text-gray-500 font-medium mb-2">Sources from TF-IDF search:</div>
                        <div className="space-y-1">
                          {message.sources.map((source, idx) => (
                            <div key={idx} className="text-xs bg-gray-50 text-gray-600 px-2 py-1 rounded flex justify-between">
                              <span>{source.metadata?.type || 'Translation'} • {source.metadata?.dialect || 'General'}</span>
                              <span className="text-gray-400">{Math.round(source.metadata?.confidence * 100) || 0}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className={`flex items-center gap-2 mt-2 ${message.role === 'user' ? 'justify-end' : ''}`}>
                    <span className="text-xs text-gray-500">{formatTime(message.timestamp)}</span>
                    {message.role === 'assistant' && (
                      <button
                        onClick={() => copyMessage(message.content)}
                        className="p-1 hover:bg-gray-100 rounded transition-colors"
                        title="Copy message"
                      >
                        <Copy className="w-3 h-3 text-gray-400" />
                      </button>
                    )}
                  </div>
                </div>

                {message.role === 'user' && (
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    </div>
                    <span className="text-sm text-gray-500">Running TF-IDF search...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="bg-white border-t border-gray-200 px-6 py-4">
            <div className="max-w-4xl mx-auto">
              <div className="flex items-end gap-3">
                <div className="flex-1 min-h-[44px] max-h-32 bg-gray-50 border border-gray-200 rounded-2xl focus-within:ring-2 focus-within:ring-green-500 focus-within:border-transparent">
                  <textarea
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask about Luhya words, translations, or cultural insights..."
                    className="w-full px-4 py-3 bg-transparent border-none outline-none resize-none text-sm placeholder-gray-500"
                    rows="1"
                    style={{ minHeight: '44px' }}
                    disabled={isLoading}
                  />
                </div>
                <button
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputText.trim()}
                  className="p-3 bg-green-500 hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-2xl transition-colors flex-shrink-0"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
              <div className="flex items-center justify-between mt-2 px-1">
                <div className="text-xs text-gray-500">
                  Press Enter to send, Shift+Enter for new line
                </div>
                <div className="text-xs text-gray-400">
                  Powered by TF-IDF • Zero Cost
                </div>
              </div>
              <div className="text-xs text-gray-400 mt-2">
                <span className="flex items-center gap-1">
                  <span className="text-gray-500">Free • TF-IDF search • Responses from Luhya multilingual dataset</span>
                 </span>
                </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LuhyaRAGChat;
