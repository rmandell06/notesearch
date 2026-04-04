import { useState } from "react";

export default function SearchBar({ onSearch, initialValue = "" }) {
  const [value, setValue] = useState(initialValue);

  function handleSubmit(e) {
    e.preventDefault();
    onSearch(value);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full" role="search">
      <div className="flex items-center border border-gray-200 rounded-lg bg-white shadow-sm focus-within:border-gray-400 focus-within:shadow-md transition-shadow">
        <span className="pl-4 text-gray-400">
          <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
        </span>
        <input
          type="search"
          aria-label="Search notes"
          placeholder="Search notes..."
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="flex-1 px-3 py-3 text-sm text-gray-800 placeholder-gray-400 bg-transparent outline-none"
        />
        {value && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setValue("")}
            className="pr-3 text-gray-300 hover:text-gray-500"
          >
            ✕
          </button>
        )}
        <button
          type="submit"
          className="m-1.5 px-4 py-1.5 bg-gray-900 text-white text-sm rounded-md hover:bg-gray-700 transition-colors"
        >
          Search
        </button>
      </div>
    </form>
  );
}
