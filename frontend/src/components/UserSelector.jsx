import React, { useState, useMemo } from 'react';

export default function UserSelector({ users, selected, onSelect, onGet }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [isOpen, setIsOpen] = useState(false);

  const filteredUsers = useMemo(() => {
    return users.filter(u => {
      const nameMatch = u.name?.toLowerCase().includes(searchTerm.toLowerCase());
      const idMatch = u.user_id?.toString().includes(searchTerm);
      return nameMatch || idMatch;
    });
  }, [users, searchTerm]);

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b border-gray-200 pb-2">User Selection</h2>
      <p className="text-sm text-gray-500 mb-4">Select a user to generate personalized movie recommendations based on their interaction history.</p>
      
      <div className="relative mb-4 flex-1">
        <label className="block text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Search User</label>
        <div className="relative">
          <input
            type="text"
            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent bg-white/50 backdrop-blur-sm transition-all"
            placeholder="Search by name or ID..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
          />
          <svg className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>

        {isOpen && filteredUsers.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-white border border-gray-100 rounded-lg shadow-lg max-h-48 overflow-y-auto">
            {filteredUsers.map(u => (
              <div
                key={u.user_id}
                className="px-4 py-2 hover:bg-indigo-50 cursor-pointer flex justify-between items-center transition-colors"
                onClick={() => {
                  onSelect(u);
                  setSearchTerm(u.name || `User ${u.user_id}`);
                  setIsOpen(false);
                }}
              >
                <span className="font-medium text-gray-800">{u.name || `User ${u.user_id}`}</span>
                <span className="text-xs text-gray-400 bg-gray-100 px-2 py-1 rounded">ID: {u.user_id}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <button 
        onClick={() => {
          setIsOpen(false);
          onGet();
        }}
        disabled={!selected}
        className={`w-full py-2.5 rounded-lg font-medium transition-all duration-200 shadow-sm ${
          selected 
            ? 'bg-indigo-600 text-white hover:bg-indigo-700 hover:shadow-indigo-200/50 hover:-translate-y-0.5' 
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
        }`}
      >
        Generate Recommendations
      </button>
    </div>
  );
}
