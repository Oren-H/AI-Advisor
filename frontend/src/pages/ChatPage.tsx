import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { MessageList } from '../components/MessageList';
import { InputBar } from '../components/InputBar';
import { useChat } from '../hooks/useChat';
import { useDarkMode } from '../hooks/useDarkMode';
import { getUserProfile } from '../api/chat';
import { UserProfileData } from '../components/ProfileForm';
import { X, RotateCcw } from 'lucide-react';

export const ChatPage: React.FC = () => {
  const {
    messages,
    isLoading,
    error,
    streamingMessageId,
    sendMessage,
    clearChat,
    retryLastMessage,
    conversationId,
    updateUserProfile,
    setConversationId,
  } = useChat();

  const { isDarkMode, toggleDarkMode } = useDarkMode();
  const [currentProfile, setCurrentProfile] = useState<UserProfileData | null>(null);
  const location = useLocation();

  // Load current profile when conversation ID is available or when returning to chat page
  useEffect(() => {
    const loadProfile = async () => {
      const savedId = conversationId || localStorage.getItem('ai-advisor-conversation-id');

      if (savedId) {
        if (!conversationId) {
          setConversationId(savedId);
        }
        try {
          const { user_profile } = await getUserProfile(savedId);
          updateUserProfile(user_profile);
          setCurrentProfile(user_profile);
          console.log('Loaded profile:', user_profile);
        } catch (err) {
          console.error('Failed to load profile:', err);
        }
      }
    };
    loadProfile();
    // Re-run when location changes (e.g., navigating back from profile page)
  }, [conversationId, updateUserProfile, setConversationId, location.pathname]);

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-gray-900 overflow-hidden">
      <Header isDarkMode={isDarkMode} onToggleDarkMode={toggleDarkMode} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar userProfile={currentProfile} />
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {/* Error Toast - Fixed position so it doesn't affect scroll layout */}
          {error && (
            <div className="absolute top-0 left-0 right-0 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-400 p-4 z-10">
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

          {/* Messages - Scrollable area */}
          <MessageList
            messages={messages}
            isLoading={isLoading}
            streamingMessageId={streamingMessageId}
          />

          {/* Input - Fixed at bottom */}
          <InputBar
            onSendMessage={(message: string) => sendMessage({ message })}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};


