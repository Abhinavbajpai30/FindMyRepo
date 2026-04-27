import { Bookmark } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '@/components/Navbar';
import RepoCard from '@/components/RepoCard';
import { useBookmarks } from '@/contexts/BookmarksContext';

const Saved = () => {
  const { bookmarks, removeBookmark } = useBookmarks();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto max-w-4xl px-4 pb-12 mt-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">Saved Repositories</h1>
          <p className="text-muted-foreground">
            {bookmarks.length} {bookmarks.length === 1 ? 'repository' : 'repositories'} saved
          </p>
        </div>

        {bookmarks.length === 0 ? (
          <div className="text-center py-20 space-y-4">
            <Bookmark className="w-12 h-12 text-muted-foreground mx-auto" />
            <p className="text-muted-foreground text-lg">No saved repositories yet.</p>
            <p className="text-sm text-muted-foreground">
              Bookmark repos from{' '}
              <Link to="/all-repos" className="text-primary hover:underline">All Repos</Link>
              {' '}or{' '}
              <Link to="/search" className="text-primary hover:underline">Search</Link>.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {bookmarks.map((repo) => (
              <RepoCard key={repo.url} repo={repo} isHighlight={false} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Saved;
