import React from 'react';
import { Sun, Moon } from 'lucide-react';

interface HeaderProps {
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
}

export const Header: React.FC<HeaderProps> = ({ isDarkMode, onToggleDarkMode }) => {
  return (
    <div className="w-full h-14 border-b border-gray-200 dark:border-gray-700 bg-[#ebf0fd] dark:bg-[#162238] flex items-center justify-between px-4">
      <div className="text-2xl font-semibold text-gray-900 dark:text-gray-100">AI Advisor</div>
      <button
        onClick={onToggleDarkMode}
        className="h-9 w-9 flex items-center justify-center rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300"
        aria-label="Toggle dark mode"
      >
        {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
      </button>
    </div>
  );
};


