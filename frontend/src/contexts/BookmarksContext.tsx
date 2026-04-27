import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { RepoData } from '@/components/RepoCard';

interface BookmarksContextType {
  bookmarks: RepoData[];
  addBookmark: (repo: RepoData) => void;
  removeBookmark: (url: string) => void;
  isBookmarked: (url: string) => boolean;
}

const BookmarksContext = createContext<BookmarksContextType | null>(null);

const STORAGE_KEY = 'savedRepos';

export const BookmarksProvider = ({ children }: { children: ReactNode }) => {
  const [bookmarks, setBookmarks] = useState<RepoData[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(bookmarks));
    } catch {
      // localStorage may be unavailable in some environments
    }
  }, [bookmarks]);

  const addBookmark = (repo: RepoData) => {
    setBookmarks(prev => {
      if (prev.some(b => b.url === repo.url)) return prev;
      return [...prev, repo];
    });
  };

  const removeBookmark = (url: string) => {
    setBookmarks(prev => prev.filter(b => b.url !== url));
  };

  const isBookmarked = (url: string) => bookmarks.some(b => b.url === url);

  return (
    <BookmarksContext.Provider value={{ bookmarks, addBookmark, removeBookmark, isBookmarked }}>
      {children}
    </BookmarksContext.Provider>
  );
};

export const useBookmarks = () => {
  const ctx = useContext(BookmarksContext);
  if (!ctx) throw new Error('useBookmarks must be used within BookmarksProvider');
  return ctx;
};
