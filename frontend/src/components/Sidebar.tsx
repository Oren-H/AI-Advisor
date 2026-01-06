import React from 'react';
import { useNavigate } from 'react-router-dom';
import { UserProfileData } from './ProfileForm';

interface SidebarProps {
  userProfile: UserProfileData | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ userProfile }) => {
  const navigate = useNavigate();
  const name = userProfile?.name || 'User';
  const initial = name?.trim()?.[0]?.toUpperCase() || 'U';

  return (
    <div className="hidden sm:flex sm:w-64 flex-col border-r border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
      <div className="flex-1" />
      <div className="px-4 py-4 flex items-center gap-3 border-t border-gray-200 dark:border-gray-700 h-[72px]">
        <div className="h-10 w-10 rounded-full bg-indigo-600 text-white flex items-center justify-center font-semibold">
          {initial}
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-gray-900 dark:text-gray-100">{name}</div>
          <button
            onClick={() => navigate('/')}
            className="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
          >
            Edit profile
          </button>
        </div>
      </div>
    </div>
  );
};


