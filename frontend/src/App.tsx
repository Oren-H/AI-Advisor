import React, { useState, useEffect } from 'react';
import { MessageList } from './components/MessageList';
import { InputBar } from './components/InputBar';
import { useChat } from './hooks/useChat';
import { X, RotateCcw } from 'lucide-react';

function App() {
  const { messages, isLoading, error, sendMessage, clearChat, retryLastMessage } = useChat();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('ai-advisor-dark-mode');
    return saved ? JSON.parse(saved) : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    localStorage.setItem('ai-advisor-dark-mode', JSON.stringify(isDarkMode));
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  return (
    <div className="h-screen flex bg-white dark:bg-gray-900">
      {/* Left Column - Branding (hidden on small screens) */}
      <div className="hidden sm:flex sm:w-80 lg:w-96 flex-col bg-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            AI Advisor
          </h1>
          <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
            Your intelligent course advisor powered by AI. Ask me anything about Columbia University courses, 
            schedules, requirements, and more.
          </p>
        </div>
        
        <div className="flex-1 p-6">
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">
              Example queries:
            </h3>
            <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
              <p>• "Find me a machine learning course in computer science"</p>
              <p>• "What are the prerequisites for Calculus I?"</p>
              <p>• "Show me courses offered on Tuesdays after 3 PM"</p>
              <p>• "What courses are available in the psychology department?"</p>
            </div>
          </div>
        </div>
        
        <div className="p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={clearChat}
            className="w-full px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Clear conversation
          </button>
        </div>
      </div>

      {/* Right Column - Chat */}
      <div className="flex-1 flex flex-col">
        {/* Error Toast */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <X className="h-5 w-5 text-red-400" />
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-800 dark:text-red-200">
                    {error}
                  </p>
                </div>
              </div>
              <button
                onClick={retryLastMessage}
                className="ml-4 flex items-center text-sm text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
              >
                <RotateCcw className="h-4 w-4 mr-1" />
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Messages */}
        <MessageList messages={messages} isLoading={isLoading} />

        {/* Input */}
        <InputBar
          onSendMessage={(message: string) => sendMessage({ message })}
          isLoading={isLoading}
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
        />
      </div>
    </div>
  );
}

export default App; 