import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export interface UserProfileData {
  major?: string;
  department_of_major?: string;
  semester?: number;
  completed_courses?: string[];
  career_goals?: string[];
  preferences?: string[];
}

interface ProfileFormProps {
  onSubmit: (profile: UserProfileData) => void;
  onClose: () => void;
  initialProfile?: UserProfileData;
}

export const ProfileForm: React.FC<ProfileFormProps> = ({
  onSubmit,
  onClose,
  initialProfile
}) => {
  const [profile, setProfile] = useState<UserProfileData>({
    major: initialProfile?.major || '',
    department_of_major: initialProfile?.department_of_major || '',
    semester: initialProfile?.semester || undefined,
    completed_courses: initialProfile?.completed_courses || [],
    career_goals: initialProfile?.career_goals || [],
    preferences: initialProfile?.preferences || [],
  });

  const [courseInput, setCourseInput] = useState('');
  const [careerGoalInput, setCareerGoalInput] = useState('');
  const [preferenceInput, setPreferenceInput] = useState('');

  // Update profile when initialProfile changes (when form reopens with saved data)
  useEffect(() => {
    if (initialProfile) {
      setProfile({
        major: initialProfile.major || '',
        department_of_major: initialProfile.department_of_major || '',
        semester: initialProfile.semester || undefined,
        completed_courses: initialProfile.completed_courses || [],
        career_goals: initialProfile.career_goals || [],
        preferences: initialProfile.preferences || [],
      });
    }
  }, [initialProfile]);

  const handleAddCourse = () => {
    if (courseInput.trim()) {
      setProfile(prev => ({
        ...prev,
        completed_courses: [...(prev.completed_courses || []), courseInput.trim().toUpperCase()]
      }));
      setCourseInput('');
    }
  };

  const handleRemoveCourse = (index: number) => {
    setProfile(prev => ({
      ...prev,
      completed_courses: prev.completed_courses?.filter((_, i) => i !== index)
    }));
  };

  const handleAddCareerGoal = () => {
    if (careerGoalInput.trim()) {
      setProfile(prev => ({
        ...prev,
        career_goals: [...(prev.career_goals || []), careerGoalInput.trim()]
      }));
      setCareerGoalInput('');
    }
  };

  const handleRemoveCareerGoal = (index: number) => {
    setProfile(prev => ({
      ...prev,
      career_goals: prev.career_goals?.filter((_, i) => i !== index)
    }));
  };

  const handleAddPreference = () => {
    if (preferenceInput.trim()) {
      setProfile(prev => ({
        ...prev,
        preferences: [...(prev.preferences || []), preferenceInput.trim()]
      }));
      setPreferenceInput('');
    }
  };

  const handleRemovePreference = (index: number) => {
    setProfile(prev => ({
      ...prev,
      preferences: prev.preferences?.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Clean up the profile - remove empty strings and undefined values
    const cleanProfile: UserProfileData = {};

    if (profile.major?.trim()) cleanProfile.major = profile.major.trim();
    if (profile.department_of_major?.trim()) cleanProfile.department_of_major = profile.department_of_major.trim().toUpperCase();
    if (profile.semester) cleanProfile.semester = profile.semester;
    if (profile.completed_courses && profile.completed_courses.length > 0) {
      cleanProfile.completed_courses = profile.completed_courses;
    }
    if (profile.career_goals && profile.career_goals.length > 0) {
      cleanProfile.career_goals = profile.career_goals;
    }
    if (profile.preferences && profile.preferences.length > 0) {
      cleanProfile.preferences = profile.preferences;
    }

    onSubmit(cleanProfile);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Your Profile
          </h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors"
          >
            <X size={20} className="text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Major */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Major
            </label>
            <input
              type="text"
              value={profile.major || ''}
              onChange={(e) => setProfile({ ...profile, major: e.target.value })}
              placeholder="e.g., Computer Science, Applied Mathematics"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Department Code
            </label>
            <input
              type="text"
              value={profile.department_of_major || ''}
              onChange={(e) => setProfile({ ...profile, department_of_major: e.target.value.toUpperCase() })}
              placeholder="e.g., COMS, MATH, PHYS"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent uppercase"
              maxLength={4}
            />
          </div>

          {/* Semester */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Current Semester (1-8)
            </label>
            <input
              type="number"
              min="1"
              max="8"
              value={profile.semester || ''}
              onChange={(e) => setProfile({ ...profile, semester: parseInt(e.target.value) || undefined })}
              placeholder="e.g., 4"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
            />
          </div>

          {/* Completed Courses */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Completed Courses
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={courseInput}
                onChange={(e) => setCourseInput(e.target.value.toUpperCase())}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCourse())}
                placeholder="e.g., COMS1004"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent uppercase"
              />
              <button
                type="button"
                onClick={handleAddCourse}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.completed_courses?.map((course, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200 rounded-full text-sm"
                >
                  {course}
                  <button
                    type="button"
                    onClick={() => handleRemoveCourse(index)}
                    className="hover:text-indigo-600 dark:hover:text-indigo-400"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Career Goals */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Career Goals
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={careerGoalInput}
                onChange={(e) => setCareerGoalInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCareerGoal())}
                placeholder="e.g., Software Engineering, Quantitative Finance"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
              />
              <button
                type="button"
                onClick={handleAddCareerGoal}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.career_goals?.map((goal, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-sm"
                >
                  {goal}
                  <button
                    type="button"
                    onClick={() => handleRemoveCareerGoal(index)}
                    className="hover:text-green-600 dark:hover:text-green-400"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Preferences */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Preferences
            </label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={preferenceInput}
                onChange={(e) => setPreferenceInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddPreference())}
                placeholder="e.g., classes after 10am, small class sizes, project-based learning"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-transparent"
              />
              <button
                type="button"
                onClick={handleAddPreference}
                className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {profile.preferences?.map((pref, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 rounded-full text-sm"
                >
                  {pref}
                  <button
                    type="button"
                    onClick={() => handleRemovePreference(index)}
                    className="hover:text-purple-600 dark:hover:text-purple-400"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors font-medium"
            >
              Save Profile
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
