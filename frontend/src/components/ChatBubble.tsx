import React from 'react';
import { Message, ToolEvent } from '../types';
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
  const [toolsOpen, setToolsOpen] = React.useState(false);
  
  return (
    <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
      {isUser ? (
        <div className="text-sm">
          {message.content}
        </div>
      ) : (
        <>
          {message.toolEvents && message.toolEvents.length > 0 && (
            <div className="mb-3 rounded border border-blue-300 bg-blue-50 dark:border-blue-600 dark:bg-blue-950">
              <button
                type="button"
                onClick={() => setToolsOpen(o => !o)}
                className="w-full text-left px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-blue-800 dark:text-blue-200"
              >
                AI tools used {toolsOpen ? '▼' : '▶'}
              </button>
              {toolsOpen && (
                <div className="px-3 py-2 space-y-2 text-xs text-blue-900 dark:text-blue-100">
                  {message.toolEvents.map((evt: ToolEvent, idx: number) => (
                    <div key={idx} className="rounded border border-blue-200/50 p-2 bg-white/40 dark:bg-blue-900/20">
                      <div className="font-mono text-[11px] mb-1">
                        <span className="font-semibold">{evt.name}</span>{' '}
                        <span className="opacity-70">({evt.kind})</span>
                      </div>
                      {'input' in evt && evt.input !== undefined && (
                        <pre className="whitespace-pre-wrap font-mono text-[11px] break-words">
                          {typeof evt.input === 'string' ? evt.input : JSON.stringify(evt.input, null, 2)}
                        </pre>
                      )}
                      {'output' in evt && evt.output !== undefined && (
                        <pre className="whitespace-pre-wrap font-mono text-[11px] break-words">
                          {evt.output}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          <StreamingText
            content={message.content}
            isStreaming={isStreaming}
          />
        </>
      )}
    </div>
  );
}; 

