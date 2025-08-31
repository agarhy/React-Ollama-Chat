import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingTimer, setLoadingTimer] = useState(0);
  const [searchEnabled, setSearchEnabled] = useState(true);
  const messagesEndRef = useRef(null);
  const timerRef = useRef(null);

  // Scroll to bottom when new messages are added
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch available models and conversations on component mount
  useEffect(() => {
    fetchModels();
    fetchConversations();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/models`);
      setModels(response.data);
      if (response.data.length > 0 && response.data[0].name) {
        setSelectedModel(response.data[0].name);
      } else {
        // Fallback to default model if no models or empty name
        setSelectedModel('phi3:mini');
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      setError('Failed to fetch available models');
      // Set default model on error
      setSelectedModel('phi3:mini');
    }
  };

  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/conversations`);
      setConversations(response.data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
    }
  };

  const loadConversation = async (convId) => {
    try {
      setIsLoading(true);
      startLoadingTimer();
      const response = await axios.get(`${API_BASE_URL}/conversations/${convId}/messages`);
      const conversationMessages = response.data.map(msg => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp
      }));
      setMessages(conversationMessages);
      setConversationId(convId);
      setError('');
    } catch (error) {
      console.error('Error loading conversation:', error);
      setError('Failed to load conversation');
    } finally {
      setIsLoading(false);
      stopLoadingTimer();
    }
  };

  const startNewConversation = () => {
    setMessages([]);
    setConversationId(null);
    setError('');
  };

  const deleteConversation = async (convId) => {
    try {
      await axios.delete(`${API_BASE_URL}/conversations/${convId}`);

      // Refresh conversations list
      fetchConversations();

      // If we deleted the current conversation, start a new one
      if (conversationId === convId) {
        startNewConversation();
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
      setError('Failed to delete conversation');
    }
  };

  const startLoadingTimer = () => {
    setLoadingTimer(0);
    timerRef.current = setInterval(() => {
      setLoadingTimer(prev => prev + 1);
    }, 1000);
  };

  const stopLoadingTimer = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setLoadingTimer(0);
  };

  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const sendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError('');
    startLoadingTimer();

    try {
      // Ensure we have a valid model selected
      const modelToUse = selectedModel && selectedModel.trim() ? selectedModel : 'phi3:mini';

      const response = await axios.post(`${API_BASE_URL}/chat`, {
        message: inputMessage,
        conversation_id: conversationId,
        model: modelToUse,
        stream: false,
        enable_search: searchEnabled
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Set conversation ID if this is the first message
      if (!conversationId) {
        setConversationId(response.data.conversation_id);
      }

      // Refresh conversations list to show new/updated conversation
      fetchConversations();

    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to get response from AI. Please try again.');
    } finally {
      setIsLoading(false);
      stopLoadingTimer();
    }
  };

  const clearConversation = async () => {
    if (conversationId) {
      try {
        await axios.delete(`${API_BASE_URL}/conversations/${conversationId}/messages`);
        fetchConversations(); // Refresh conversations list
      } catch (error) {
        console.error('Error clearing conversation:', error);
      }
    }
    setMessages([]);
    setConversationId(null);
    setError('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="h-screen bg-base-100 flex overflow-hidden">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 overflow-hidden bg-base-200 border-r border-base-300`}>
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Conversations</h2>
            <button
              className="btn btn-sm btn-primary"
              onClick={startNewConversation}
            >
              New Chat
            </button>
          </div>

          <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`p-3 rounded-lg transition-colors group ${
                  conversationId === conv.id
                    ? 'bg-primary text-primary-content'
                    : 'bg-base-100 hover:bg-base-300'
                }`}
              >
                <div
                  className="cursor-pointer"
                  onClick={() => loadConversation(conv.id)}
                >
                  <div className="font-medium text-sm truncate">
                    {conv.title || `Chat ${conv.id.slice(0, 8)}`}
                  </div>
                  <div className="text-xs opacity-70 mt-1">
                    {new Date(conv.updated_at).toLocaleDateString()}
                  </div>
                </div>
                <div className="flex justify-end mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    className="btn btn-ghost btn-xs text-error hover:bg-error hover:text-error-content"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm('Are you sure you want to delete this conversation?')) {
                        deleteConversation(conv.id);
                      }
                    }}
                    title="Delete conversation"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
            {conversations.length === 0 && (
              <div className="text-center text-base-content/50 py-8">
                No conversations yet
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Header */}
        <header className="navbar bg-primary text-primary-content shadow-lg">
          <div className="flex-1">
            <button
              className="btn btn-ghost btn-sm mr-2"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            <h1 className="text-xl font-bold">AI Chat</h1>
          </div>
          <div className="flex-none gap-2">
            {/* Search Toggle */}
            <div className="form-control">
              <label className="label cursor-pointer">
                <span className="label-text text-primary-content mr-2">Search Online</span>
                <input
                  type="checkbox"
                  className="toggle toggle-sm"
                  checked={searchEnabled}
                  onChange={(e) => setSearchEnabled(e.target.checked)}
                  disabled={isLoading}
                />
              </label>
            </div>

            {/* Model Selection */}
            <div className="form-control">
              <select
                className="select select-bordered select-sm"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isLoading}
              >
                {models.length > 0 ? (
                  models.map((model) => (
                    <option key={model.name || 'unknown'} value={model.name || ''}>
                      {model.name || 'Unknown Model'}
                    </option>
                  ))
                ) : (
                  <option value="phi3:mini">phi3:mini (default)</option>
                )}
              </select>
            </div>

            {/* Clear Button */}
            <button
              className="btn btn-ghost btn-sm"
              onClick={clearConversation}
              disabled={isLoading || messages.length === 0}
            >
              Clear
            </button>
          </div>
        </header>

      {/* Chat Messages */}
      <main className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 overflow-y-auto p-4 chat-container">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-base-content/70 mb-2">
                  Welcome to AI Chat
                </h2>
                <p className="text-base-content/50">
                  Start a conversation with your AI assistant
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`chat ${message.role === 'user' ? 'chat-end' : 'chat-start'}`}
                >
                  <div className="chat-image avatar">
                    <div className="w-10 rounded-full">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${
                        message.role === 'user' ? 'bg-primary' : 'bg-secondary'
                      }`}>
                        {message.role === 'user' ? 'U' : 'AI'}
                      </div>
                    </div>
                  </div>
                  <div className="chat-header">
                    {message.role === 'user' ? 'You' : 'Assistant'}
                    <time className="text-xs opacity-50 ml-1">
                      {formatTimestamp(message.timestamp)}
                    </time>
                  </div>
                  <div className={`chat-bubble ${
                    message.role === 'user' ? 'chat-bubble-primary' : 'chat-bubble-secondary'
                  }`}>
                    <div className="whitespace-pre-wrap">{message.content}</div>
                  </div>
                </div>
              ))}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="chat chat-start">
                  <div className="chat-image avatar">
                    <div className="w-10 rounded-full">
                      <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold bg-secondary">
                        AI
                      </div>
                    </div>
                  </div>
                  <div className="chat-header">
                    Assistant
                    <time className="text-xs opacity-50 ml-1">
                      {loadingTimer}s
                    </time>
                  </div>
                  <div className="chat-bubble chat-bubble-secondary">
                    <div className="flex items-center space-x-2">
                      <span className="loading loading-dots loading-sm"></span>
                      <span>Thinking...</span>
                      <div className="text-xs opacity-70">
                        {loadingTimer < 5 ? 'Processing...' :
                         loadingTimer < 10 ? 'Generating response...' :
                         loadingTimer < 20 ? 'Almost done...' :
                         'This is taking longer than usual...'}
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="alert alert-error mx-4 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>{error}</span>
          </div>
        )}

        {/* Input Area */}
        <footer className="p-4 bg-base-200 border-t flex-shrink-0">
          <div className="flex gap-2">
            <textarea
              className="textarea textarea-bordered flex-1 resize-none"
              placeholder="Type your message here..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              rows="1"
            />
            <button
              className="btn btn-primary"
              onClick={sendMessage}
              disabled={!inputMessage.trim() || isLoading}
            >
              {isLoading ? (
                <span className="loading loading-spinner loading-sm"></span>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              )}
            </button>
          </div>
        </footer>
      </main>
      </div>
    </div>
  );
}

export default App;
