import { useState, useEffect } from 'react';
import { MessageList } from './components/MessageList';
import { InputBar } from './components/InputBar';
import { ProfileForm, UserProfileData } from './components/ProfileForm';
import { useChat } from './hooks/useChat';
import { initializeUserProfile, updateUserProfile, getUserProfile } from './api/chat';
import { X, RotateCcw, User } from 'lucide-react';

function App() {
  const { messages, isLoading, error, streamingMessageId, sendMessage, clearChat, retryLastMessage, conversationId, updateUserProfile: updateChatProfile, setConversationId } = useChat();
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem('ai-advisor-dark-mode');
    return saved ? JSON.parse(saved) : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [showProfileForm, setShowProfileForm] = useState(false);
  const [currentProfile, setCurrentProfile] = useState<UserProfileData | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  useEffect(() => {
    localStorage.setItem('ai-advisor-dark-mode', JSON.stringify(isDarkMode));
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Load current profile when conversation ID is available
  useEffect(() => {
    const loadProfile = async () => {
      if (conversationId) {
        try {
          const { user_profile } = await getUserProfile(conversationId);
          setCurrentProfile(user_profile);
        } catch (err) {
          console.error('Failed to load profile:', err);
        }
      }
    };
    loadProfile();
  }, [conversationId]);

  const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

  const handleProfileSubmit = async (profile: UserProfileData) => {
    setProfileError(null);

    try {
      if (conversationId) {
        // Try to update existing profile
        try {
          const result = await updateUserProfile(conversationId, profile);
          setCurrentProfile(result.user_profile);
          updateChatProfile(result.user_profile);
        } catch (updateErr) {
          // If conversation doesn't exist on backend (404), initialize new one
          console.log('Conversation not found on backend, initializing new one');
          const result = await initializeUserProfile(profile);
          setCurrentProfile(result.user_profile);
          updateChatProfile(result.user_profile);
          setConversationId(result.conversation_id);
        }
      } else {
        // Initialize new conversation with profile
        const result = await initializeUserProfile(profile);
        setCurrentProfile(result.user_profile);
        updateChatProfile(result.user_profile);
        setConversationId(result.conversation_id);
      }
      setShowProfileForm(false);
    } catch (err) {
      setProfileError(err instanceof Error ? err.message : 'Failed to save profile');
    }
  };

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
        
        <div className="p-6 border-t border-gray-200 dark:border-gray-700 space-y-2">
          <button
            onClick={() => setShowProfileForm(true)}
            className="w-full px-3 py-2 text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <User size={16} />
            {currentProfile?.major ? 'Edit Profile' : 'Set Up Profile'}
          </button>
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
        <MessageList 
          messages={messages} 
          isLoading={isLoading} 
          streamingMessageId={streamingMessageId}
        />

        {/* Input */}
        <InputBar
          onSendMessage={(message: string) => sendMessage({ message })}
          isLoading={isLoading}
          isDarkMode={isDarkMode}
          onToggleDarkMode={toggleDarkMode}
        />
      </div>

      {/* Profile Form Modal */}
      {showProfileForm && (
        <ProfileForm
          onSubmit={handleProfileSubmit}
          onClose={() => {
            setShowProfileForm(false);
            setProfileError(null);
          }}
          initialProfile={currentProfile || undefined}
        />
      )}

      {/* Profile Error Toast */}
      {profileError && (
        <div className="fixed bottom-4 right-4 bg-red-50 dark:bg-red-900/20 border border-red-400 rounded-lg p-4 shadow-lg max-w-md">
          <div className="flex items-start justify-between">
            <div className="flex items-center">
              <X className="h-5 w-5 text-red-400 mr-2" />
              <p className="text-sm text-red-800 dark:text-red-200">
                {profileError}
              </p>
            </div>
            <button
              onClick={() => setProfileError(null)}
              className="ml-4 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 