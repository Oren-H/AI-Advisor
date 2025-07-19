import { useState, useCallback, useEffect } from 'react';
import { Message, ChatState, SendMessageParams } from '../types';
import { sendMessage } from '../api/chat';

// Local storage key for persisting chat history
const CHAT_STORAGE_KEY = 'ai-advisor-chat-history';

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });

  // Load chat history from localStorage on mount
  useEffect(() => {
    const savedChat = localStorage.getItem(CHAT_STORAGE_KEY);
    if (savedChat) {
      try {
        const parsed = JSON.parse(savedChat);
        const messages = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setState(prev => ({ ...prev, messages }));
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
  }, []);

  // Save chat history to localStorage whenever messages change
  useEffect(() => {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(state.messages));
  }, [state.messages]);

  const addMessage = useCallback((message: Message) => {
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
      error: null,
    }));
  }, []);

  const updateLastMessage = useCallback((content: string) => {
    setState(prev => ({
      ...prev,
      messages: prev.messages.map((msg, index) =>
        index === prev.messages.length - 1
          ? { ...msg, content }
          : msg
      ),
    }));
  }, []);

  const sendUserMessage = useCallback(async (params: SendMessageParams) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      content: params.message,
      role: 'user',
      timestamp: new Date(),
    };

    addMessage(userMessage);

    // Add placeholder assistant message
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      content: '',
      role: 'assistant',
      timestamp: new Date(),
    };

    addMessage(assistantMessage);
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      await sendMessage(params.message, (token) => {
        updateLastMessage(assistantMessage.content + token);
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to send message',
      }));
      // Remove the failed assistant message
      setState(prev => ({
        ...prev,
        messages: prev.messages.filter(msg => msg.id !== assistantMessage.id),
      }));
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, [addMessage, updateLastMessage]);

  const clearChat = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      error: null,
    });
    localStorage.removeItem(CHAT_STORAGE_KEY);
  }, []);

  const retryLastMessage = useCallback(() => {
    const lastUserMessage = state.messages
      .filter(msg => msg.role === 'user')
      .pop();
    
    if (lastUserMessage) {
      sendUserMessage({ message: lastUserMessage.content });
    }
  }, [state.messages, sendUserMessage]);

  return {
    ...state,
    sendMessage: sendUserMessage,
    clearChat,
    retryLastMessage,
  };
}; 