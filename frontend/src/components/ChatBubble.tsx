import React from 'react';
import { Message } from '../types';
import { StreamingText } from './StreamingText';

interface ChatBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ 
  message, 
  isStreaming = false
}) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
      {isUser ? (
        <div className="text-sm">
          {message.content}
        </div>
      ) : (
        <StreamingText 
          content={message.content}
          isStreaming={isStreaming}
        />
      )}
    </div>
  );
}; 