import { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from './ui/button';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  className?: string;
}

const SearchBar = ({ onSearch, placeholder = "Find beginner-friendly Python repos with good first issues", className = "" }: SearchBarProps) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query);
    }
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <div className="relative flex items-center gap-2 bg-card rounded-xl border border-border p-2 shadow-md hover:shadow-lg transition-all duration-300">
        <Search className="h-5 w-5 text-muted-foreground ml-2" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder}
          className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground px-2 py-2"
        />
        <Button type="submit" size="sm" variant="hero">
          Search
        </Button>
      </div>
    </form>
  );
};

export default SearchBar;
