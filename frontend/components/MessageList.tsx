import React, { useRef, useEffect } from 'react';
import { Message } from '../types';
import { ChatBubble } from './ChatBubble';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  streamingMessageId?: string | null;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, isLoading, streamingMessageId }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.map((message) => (
        <ChatBubble 
          key={message.id} 
          message={message} 
          isStreaming={message.id === streamingMessageId}
        />
      ))}
      
      {isLoading && !streamingMessageId && (
        <div className="typing-indicator">
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
          <div className="typing-dot"></div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
}; 