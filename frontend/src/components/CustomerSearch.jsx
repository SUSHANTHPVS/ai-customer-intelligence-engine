import React, { useState, useEffect } from 'react';
import { Search, ChevronDown } from 'react-icons/fa';

const CustomerSearch = ({ onSelectCustomer }) => {
  const [searchInput, setSearchInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Generate sample customer suggestions for demo
  const generateSuggestions = (input) => {
    if (!input) return [];
    
    const prefix = input.slice(0, 1); // C or c
    const num = parseInt(input.slice(1)) || 0;
    
    const suggestions = [];
    for (let i = Math.max(0, num - 2); i <= Math.min(9999, num + 2); i++) {
      if (i >= 0) {
        suggestions.push(`C${String(i).padStart(6, '0')}`);
      }
    }
    return suggestions;
  };

  useEffect(() => {
    const upInput = searchInput.toUpperCase();
    if (upInput.startsWith('C') && upInput.length >= 2) {
      setSuggestions(generateSuggestions(upInput));
      setShowSuggestions(true);
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }
  }, [searchInput]);

  const handleSearch = (customerId) => {
    onSelectCustomer(customerId);
    setSearchInput('');
    setShowSuggestions(false);
  };

  const handleQuickSelect = () => {
    // Select a random customer for demo
    const randomId = `C${String(Math.floor(Math.random() * 10000)).padStart(6, '0')}`;
    handleSearch(randomId);
  };

  return (
    <div className="relative">
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <input
            type="text"
            placeholder="Enter customer ID (e.g., C000001)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && searchInput.trim()) {
                handleSearch(searchInput.toUpperCase());
              }
            }}
            className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/20"
          />
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-700 border border-slate-600 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto">
              {suggestions.map((id) => (
                <button
                  key={id}
                  onClick={() => handleSearch(id)}
                  className="w-full text-left px-4 py-2 hover:bg-slate-600 text-white transition"
                >
                  {id}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => {
            if (searchInput.trim()) {
              handleSearch(searchInput.toUpperCase());
            }
          }}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition flex items-center gap-2"
        >
          <Search size={18} /> Search
        </button>

        <button
          onClick={handleQuickSelect}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-semibold transition"
        >
          Random
        </button>
      </div>

      {/* Quick Links */}
      <div className="mt-4 grid grid-cols-3 gap-2">
        {['C000001', 'C000500', 'C001000'].map((id) => (
          <button
            key={id}
            onClick={() => handleSearch(id)}
            className="px-3 py-1 text-sm bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition"
          >
            {id}
          </button>
        ))}
      </div>
    </div>
  );
};

export default CustomerSearch;
