import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Bookmark } from 'lucide-react';
import { useBookmarks } from '@/contexts/BookmarksContext';

const Navbar = () => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { bookmarks } = useBookmarks();

  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/all-repos', label: 'All Repos' },
    { path: '/hidden-gems', label: 'Hidden Gems' },
    { path: '/hacktoberfest', label: 'Hacktoberfest' },
    { path: '/saved', label: 'Saved' },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/50">
      <div className="container-modern">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group" onClick={() => setMobileOpen(false)}>
            <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider group-hover:text-foreground transition-colors duration-300 code-text">
              FindMy Repo
            </span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(({ path, label }) => (
              <Link
                key={path}
                to={path}
                className={`relative flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  isActive(path)
                    ? 'text-foreground bg-secondary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                }`}
              >
                <span className="code-text">{label}</span>
                {path === '/saved' && bookmarks.length > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 flex items-center justify-center bg-primary text-primary-foreground text-[10px] font-bold rounded-full">
                    {bookmarks.length > 9 ? '9+' : bookmarks.length}
                  </span>
                )}
              </Link>
            ))}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setMobileOpen(prev => !prev)}
              className="px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors duration-300"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        {mobileOpen && (
          <div className="md:hidden border-t border-border/50 py-3 space-y-1">
            {navItems.map(({ path, label }) => (
              <Link
                key={path}
                to={path}
                onClick={() => setMobileOpen(false)}
                className={`relative flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive(path)
                    ? 'text-foreground bg-secondary'
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                }`}
              >
                <span className="code-text">{label}</span>
                {path === '/saved' && bookmarks.length > 0 && (
                  <span className="ml-auto w-5 h-5 flex items-center justify-center bg-primary text-primary-foreground text-[10px] font-bold rounded-full">
                    {bookmarks.length > 9 ? '9+' : bookmarks.length}
                  </span>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
