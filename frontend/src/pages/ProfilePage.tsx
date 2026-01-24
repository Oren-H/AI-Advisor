import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProfileForm, UserProfileData } from '../components/ProfileForm';
import { initializeUserProfile, updateUserProfile, getUserProfile } from '../api/chat';
import { useDarkMode } from '../hooks/useDarkMode';

const CONVERSATION_ID_KEY = 'ai-advisor-conversation-id';

export const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [initialProfile, setInitialProfile] = useState<UserProfileData | undefined>(undefined);
  const { isDarkMode } = useDarkMode(); // ensure dark mode class applied if persisted

  // Load existing profile if available
  useEffect(() => {
    const loadProfile = async () => {
      const existingConversationId = localStorage.getItem(CONVERSATION_ID_KEY);
      console.log('ProfilePage - Loading profile for conversation:', existingConversationId);
      if (existingConversationId) {
        try {
          const { user_profile } = await getUserProfile(existingConversationId);
          console.log('ProfilePage - Loaded profile:', user_profile);
          setInitialProfile(user_profile);
        } catch (err) {
          console.error('Failed to load profile:', err);
        }
      }
    };
    loadProfile();
  }, []);

  const handleSubmit = async (profile: UserProfileData) => {
    setError(null);
    console.log('Saving profile:', profile);
    try {
      const existingConversationId = localStorage.getItem(CONVERSATION_ID_KEY) || undefined;

      if (existingConversationId) {
        try {
          const result = await updateUserProfile(existingConversationId, profile);
          localStorage.setItem(CONVERSATION_ID_KEY, result.conversation_id);
          console.log('Profile updated:', result);
        } catch {
          const result = await initializeUserProfile(profile);
          localStorage.setItem(CONVERSATION_ID_KEY, result.conversation_id);
          console.log('Profile initialized:', result);
        }
      } else {
        const result = await initializeUserProfile(profile);
        localStorage.setItem(CONVERSATION_ID_KEY, result.conversation_id);
        console.log('Profile initialized:', result);
      }

      navigate('/chat');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save profile');
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900 flex items-center justify-center p-2">
      {/* Render the ProfileForm with solid background */}
      <ProfileForm
        onSubmit={handleSubmit}
        onClose={() => navigate('/chat')}
        initialProfile={initialProfile}
        showOverlay={false}
      />

      {error && (
        <div className="fixed bottom-4 right-4 bg-red-50 dark:bg-red-900/20 border border-red-400 rounded-lg p-4 shadow-lg max-w-md">
          <p className="text-sm text-red-800 dark:text-red-200">
            {error}
          </p>
        </div>
      )}
    </div>
  );
};


