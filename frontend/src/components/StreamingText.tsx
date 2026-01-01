import React from 'react';

interface StreamingTextProps {
  content: string;
  isStreaming?: boolean;
}

export const StreamingText: React.FC<StreamingTextProps> = ({ content }) => {
  return (
    <div className="text-sm whitespace-pre-wrap">
      {content}
    </div>
  );
};


