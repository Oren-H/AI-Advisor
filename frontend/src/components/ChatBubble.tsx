import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
      {isUser ? (
        <div className="text-sm">
          {message.content}
        </div>
      ) : (
        <ReactMarkdown 
          className="prose prose-sm dark:prose-invert max-w-none"
          components={{
            // Customize markdown components for better styling
            p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
            code: ({ children, className }) => (
              <code className={`${className} bg-gray-100 dark:bg-gray-800 px-1 py-0.5 rounded text-sm`}>
                {children}
              </code>
            ),
            pre: ({ children }) => (
              <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg overflow-x-auto text-sm">
                {children}
              </pre>
            ),
            ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
          }}
        >
          {message.content}
        </ReactMarkdown>
      )}
    </div>
  );
}; 