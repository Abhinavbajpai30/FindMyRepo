import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export interface UserPreferences {
  skillLevel: string;
  languages: string[];
  interestAreas: string[];
  contributionIntent: string;
  timeAvailability: string;
}

interface PreferencesContextType {
  preferences: UserPreferences | null;
  setPreferences: (prefs: UserPreferences) => void;
  hasCompletedOnboarding: boolean;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

export const PreferencesProvider = ({ children }: { children: ReactNode }) => {
  const [preferences, setPreferencesState] = useState<UserPreferences | null>(() => {
    const saved = localStorage.getItem('userPreferences');
    return saved ? JSON.parse(saved) : null;
  });

  const setPreferences = (prefs: UserPreferences) => {
    setPreferencesState(prefs);
    localStorage.setItem('userPreferences', JSON.stringify(prefs));
  };

  const hasCompletedOnboarding = preferences !== null;

  return (
    <PreferencesContext.Provider value={{ preferences, setPreferences, hasCompletedOnboarding }}>
      {children}
    </PreferencesContext.Provider>
  );
};

export const usePreferences = () => {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used within PreferencesProvider');
  }
  return context;
};
