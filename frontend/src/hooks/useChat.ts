import { useState, useCallback, useEffect } from 'react';
import { Message, ChatState, SendMessageParams, ChatResponse } from '../types';
import { sendMessage } from '../api/chat';

// Local storage key for persisting chat history
const CHAT_STORAGE_KEY = 'ai-advisor-chat-history';
const CONVERSATION_ID_KEY = 'ai-advisor-conversation-id';

export const useChat = () => {
  const [state, setState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
    conversationId: undefined,
    userProfile: {},
  });

  // Load chat history and conversation ID from localStorage on mount
  useEffect(() => {
    const savedChat = localStorage.getItem(CHAT_STORAGE_KEY);
    const savedConversationId = localStorage.getItem(CONVERSATION_ID_KEY);
    
    if (savedChat) {
      try {
        const parsed = JSON.parse(savedChat);
        const messages = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setState(prev => ({ 
          ...prev, 
          messages,
          conversationId: savedConversationId || undefined
        }));
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
  }, []);

  // Save chat history and conversation ID to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(state.messages));
    if (state.conversationId) {
      localStorage.setItem(CONVERSATION_ID_KEY, state.conversationId);
    }
  }, [state.messages, state.conversationId]);

  const addMessage = useCallback((message: Message) => {
    setState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
      error: null,
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
      // Prepare the request
      const request = {
        message: params.message,
        conversation_id: params.conversationId || state.conversationId,
        user_profile: params.userProfile || state.userProfile,
      };

      const response: ChatResponse = await sendMessage(request);
      
      // Update the assistant message with the response
      setState(prev => ({
        ...prev,
        messages: prev.messages.map((msg, index) =>
          index === prev.messages.length - 1
            ? { ...msg, content: response.response }
            : msg
        ),
        conversationId: response.conversation_id,
        userProfile: { ...prev.userProfile, ...response.filters },
        isLoading: false,
      }));

      // Log additional information for debugging
      if (response.course_results && response.course_results.length > 0) {
        console.log('Course results:', response.course_results);
      }
      if (response.filters) {
        console.log('Applied filters:', response.filters);
      }
      console.log('Intent:', response.intent);

    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to send message',
        isLoading: false,
      }));
      // Remove the failed assistant message
      setState(prev => ({
        ...prev,
        messages: prev.messages.filter(msg => msg.id !== assistantMessage.id),
      }));
    }
  }, [addMessage, state.conversationId, state.userProfile]);

  const clearChat = useCallback(() => {
    setState({
      messages: [],
      isLoading: false,
      error: null,
      conversationId: undefined,
      userProfile: {},
    });
    localStorage.removeItem(CHAT_STORAGE_KEY);
    localStorage.removeItem(CONVERSATION_ID_KEY);
  }, []);

  const retryLastMessage = useCallback(() => {
    const lastUserMessage = state.messages
      .filter(msg => msg.role === 'user')
      .pop();
    
    if (lastUserMessage) {
      sendUserMessage({ message: lastUserMessage.content });
    }
  }, [state.messages, sendUserMessage]);

  const updateUserProfile = useCallback((profile: Record<string, any>) => {
    setState(prev => ({
      ...prev,
      userProfile: { ...prev.userProfile, ...profile },
    }));
  }, []);

  return {
    ...state,
    sendMessage: sendUserMessage,
    clearChat,
    retryLastMessage,
    updateUserProfile,
  };
}; 