import { Badge } from './ui/badge';
import { Star, Clock, ExternalLink, GitBranch, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';

export interface RepoData {
  name: string;
  description: string;
  languages: string[];
  stars: number;
  lastActivity: string;
  issues: number;
  charging: 'active' | 'medium' | 'inactive';
  url: string;
  owner?: string;
}

interface RepoCardProps {
  repo: RepoData;
  isHighlight?: boolean;
}

// Charging status color mapping
const getChargingColor = (status: 'active' | 'medium' | 'inactive') => {
  const colors = {
    'active': 'bg-green-500',
    'medium': 'bg-yellow-500', 
    'inactive': 'bg-red-500'
  };
  return colors[status];
};

// Language color mapping
const getLanguageColor = (language: string) => {
  const colors: Record<string, string> = {
    'JavaScript': 'bg-yellow-500',
    'TypeScript': 'bg-blue-500',
    'Python': 'bg-green-500',
    'HTML': 'bg-orange-500',
    'CSS': 'bg-blue-400',
    'Java': 'bg-red-500',
    'C++': 'bg-blue-600',
    'Go': 'bg-cyan-500',
    'Rust': 'bg-orange-600',
    'PHP': 'bg-purple-500',
    'Ruby': 'bg-red-400',
    'Swift': 'bg-orange-400',
    'Kotlin': 'bg-purple-600',
    'Dart': 'bg-blue-500',
    'C#': 'bg-purple-700',
    'Scala': 'bg-red-600',
    'Shell': 'bg-gray-600',
    'PowerShell': 'bg-blue-700',
    'Vue': 'bg-green-400',
    'React': 'bg-cyan-400',
    'Angular': 'bg-red-500',
    'Svelte': 'bg-orange-500',
    'Markdown': 'bg-gray-500',
    'YAML': 'bg-red-500',
    'JSON': 'bg-yellow-600',
    'XML': 'bg-orange-600',
    'SQL': 'bg-blue-600',
    'R': 'bg-blue-400',
    'MATLAB': 'bg-orange-500',
    'Perl': 'bg-purple-500',
    'Haskell': 'bg-purple-600',
    'Clojure': 'bg-green-600',
    'Erlang': 'bg-red-500',
    'Elixir': 'bg-purple-500',
    'F#': 'bg-blue-500',
    'OCaml': 'bg-orange-500',
    'Reason': 'bg-red-500',
    'Nim': 'bg-yellow-500',
    'Crystal': 'bg-gray-600',
    'Julia': 'bg-purple-500',
    'Lua': 'bg-blue-400',
    'Pascal': 'bg-blue-600',
    'Ada': 'bg-blue-500',
    'Fortran': 'bg-green-600',
    'COBOL': 'bg-blue-700',
    'Assembly': 'bg-gray-600',
    'Vim script': 'bg-green-500',
    'Emacs Lisp': 'bg-purple-500',
    'TeX': 'bg-gray-600',
    'Jupyter Notebook': 'bg-orange-500',
    'Makefile': 'bg-gray-600',
    'CMake': 'bg-blue-600',
    'Groovy': 'bg-blue-500',
    'Objective-C': 'bg-blue-600',
    'Objective-C++': 'bg-blue-700',
    'CoffeeScript': 'bg-yellow-600',
    'LiveScript': 'bg-blue-500',
    'D': 'bg-red-500',
    'Vala': 'bg-purple-500',
    'Racket': 'bg-blue-500',
    'Scheme': 'bg-red-500',
    'Common Lisp': 'bg-purple-600',
    'AutoHotkey': 'bg-green-500',
    'AutoIt': 'bg-green-600',
    'Batchfile': 'bg-gray-600',
    'VimL': 'bg-green-500',
    'Zig': 'bg-orange-500',
    'Nix': 'bg-blue-500',
    'Solidity': 'bg-gray-600',
    'WebAssembly': 'bg-purple-500',
    'GraphQL': 'bg-pink-500',
    'Handlebars': 'bg-orange-500',
    'Mustache': 'bg-gray-600',
    'Twig': 'bg-green-500',
    'Jinja': 'bg-red-500',
    'Pug': 'bg-green-600',
    'Stylus': 'bg-yellow-500',
    'Sass': 'bg-pink-500',
    'SCSS': 'bg-pink-500',
    'Less': 'bg-blue-500',
    'PostCSS': 'bg-purple-500',
  };
  
  return colors[language] || 'bg-gray-500';
};

const RepoCard = ({ repo, isHighlight = false }: RepoCardProps) => {
  const formatLastActivity = (lastActivity: string) => {
    try {
      // Check if it's an ISO date format
      if (lastActivity.includes('T') && lastActivity.includes('Z')) {
        const date = new Date(lastActivity);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
        
        if (diffInSeconds < 60) {
          return 'Just now';
        } else if (diffInSeconds < 3600) {
          const minutes = Math.floor(diffInSeconds / 60);
          return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 86400) {
          const hours = Math.floor(diffInSeconds / 3600);
          return `${hours} hour${hours > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 2592000) {
          const days = Math.floor(diffInSeconds / 86400);
          return `${days} day${days > 1 ? 's' : ''} ago`;
        } else if (diffInSeconds < 31536000) {
          const months = Math.floor(diffInSeconds / 2592000);
          return `${months} month${months > 1 ? 's' : ''} ago`;
        } else {
          const years = Math.floor(diffInSeconds / 31536000);
          return `${years} year${years > 1 ? 's' : ''} ago`;
        }
      }
      // If it's already in a readable format, return as is
      return lastActivity;
    } catch (error) {
      // If parsing fails, return the original string
      return lastActivity;
    }
  };

  return (
    <article 
      className={`group bg-card border border-border rounded-xl p-5 hover:border-primary/30 hover:shadow-lg transition-all duration-300 cursor-pointer ${isHighlight ? 'border-primary/40 bg-primary/5' : ''}`}
      onClick={() => window.open(repo.url, '_blank')}
    >
      {/* Header with name and charging status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-4">
            <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors truncate">
              {(() => {
                try {
                  const url = new URL(repo.url);
                  const pathParts = url.pathname.split('/').filter(part => part);
                  if (pathParts.length >= 2) {
                    return `${pathParts[0]}/${pathParts[1]}`;
                  }
                  return repo.name;
                } catch {
                  return repo.name;
                }
              })()}
            </h3>
            {/* Charging status indicator */}
            <div className="flex items-center gap-1.5 px-2 py-1 bg-muted/50 rounded-full">
              <div className={`w-2 h-2 rounded-full ${getChargingColor(repo.charging)}`}></div>
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                {repo.charging}
              </span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed mb-4 min-h-[2.5rem]">
            {repo.description}
          </p>
        </div>
        
        <Button 
          variant="ghost"
          size="sm"
          className="h-8 w-8 p-0 text-muted-foreground hover:text-primary flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            window.open(repo.url, '_blank');
          }}
        >
          <ExternalLink className="h-4 w-4" />
        </Button>
      </div>

      {/* Languages */}
      <div className="flex flex-wrap gap-2 mb-4">
        {repo.languages.slice(0, 3).map((language) => (
          <div key={language} className="flex items-center gap-1.5 pl-1 pr-2 py-1.5 bg-muted/30 rounded-md">
            <div className={`w-2 h-2 rounded-full ${getLanguageColor(language)}`} />
            <span className="text-xs font-medium text-muted-foreground">{language}</span>
          </div>
        ))}
        {repo.languages.length > 3 && (
          <div className="pl-1 pr-2 py-1.5 bg-muted/20 rounded-md">
            <span className="text-xs font-medium text-muted-foreground">+{repo.languages.length - 3}</span>
          </div>
        )}
      </div>
      
      {/* Footer stats */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Star className="h-4 w-4" />
            <span className="font-medium">{repo.stars.toLocaleString()} stars</span>
          </div>
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <AlertCircle className="h-4 w-4" />
            <span className="font-medium">{repo.issues} issues</span>
          </div>
        </div>
        
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <Clock className="h-4 w-4" />
          <span className="text-xs">Updated {formatLastActivity(repo.lastActivity)}</span>
        </div>
      </div>
    </article>
  );
};

export default RepoCard;
