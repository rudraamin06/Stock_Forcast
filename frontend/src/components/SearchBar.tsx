import React, { useState } from "react";

// Common stock tickers and ETFs
const TICKERS = [
  // Major ETFs
  "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "VGT", "XLF", "XLE", "XLK",
  // Major Tech Stocks
  "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "AMD", "INTC",
  // Financial Stocks
  "JPM", "BAC", "GS", "MS", "V", "MA", "AXP", "BLK", "C", "WFC",
  // Other Popular Stocks
  "WMT", "DIS", "KO", "PEP", "CSCO", "VZ", "UBER", "ABNB", "NKE", "MCD"
];

interface SearchBarProps {
  onSelect: (ticker: string) => void;
}

export default function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.toUpperCase();
    setQuery(value);
    if (value.length === 0) {
      setSuggestions([]);
    } else {
      setSuggestions(TICKERS.filter(ticker => ticker.startsWith(value)));
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && query.trim()) {
      onSelect(query.trim().toUpperCase());
      setSuggestions([]);
    }
  };

  const handleSuggestionClick = (ticker: string) => {
    setQuery(ticker);
    setSuggestions([]);
    onSelect(ticker);
  };

  return (
    <div className="search-container">
      <input
        type="text"
        value={query}
        onChange={handleInputChange}
        onKeyPress={handleKeyPress}
        placeholder="Enter stock ticker (e.g., AAPL) and press Enter"
        className="search-input"
      />
      {suggestions.length > 0 && (
        <ul className="suggestions-list">
          {suggestions.map(ticker => (
            <li
              key={ticker}
              onClick={() => handleSuggestionClick(ticker)}
              className="suggestion-item"
            >
              {ticker}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
