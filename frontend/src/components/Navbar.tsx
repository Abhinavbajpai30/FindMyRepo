import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const location = useLocation();
  
  const isActive = (path: string) => location.pathname === path;

  const navItems = [
    { path: '/all-repos', label: 'All Repos' },
    { path: '/hidden-gems', label: 'Hidden Gems' },
  ];

  return (
    <nav className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border/50">
      <div className="container-modern">
        <div className="flex items-center justify-between h-16">
          {/* Logo - Leftmost */}
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider group-hover:text-foreground transition-colors duration-300 code-text">
              FindMy Repo
            </span>
          </Link>
          
          {/* Navigation Links - Right */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(({ path, label }) => (
              <Link 
                key={path}
                to={path} 
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  isActive(path)
                    ? 'text-foreground bg-secondary' 
                    : 'text-muted-foreground hover:text-foreground hover:bg-secondary/50'
                }`}
              >
                <span className="code-text">{label}</span>
              </Link>
            ))}
          </div>

          {/* Mobile Menu Button - Rightmost */}
          <div className="md:hidden">
            <button 
              className="px-3 py-2 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-secondary/50 transition-colors duration-300"
              aria-label="Open mobile menu"
            >
              Menu
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
