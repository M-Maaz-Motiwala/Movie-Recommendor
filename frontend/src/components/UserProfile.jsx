import React from 'react';

export default function UserProfile({ user }) {
  if (!user) {
    return (
      <div className="glass-card p-6 h-full flex flex-col items-center justify-center text-gray-400">
        <svg className="w-12 h-12 mb-3 text-indigo-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
        <p>Please select a user to view their profile</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 h-full flex flex-col">
      <h2 className="text-xl font-bold text-gray-800 mb-4 border-b border-gray-200 pb-2">User Context</h2>
      
      <div className="flex items-center gap-4 mb-6">
        <div className="w-16 h-16 rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold shadow-md">
          {user.name ? user.name.charAt(0).toUpperCase() : 'U'}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{user.name || `User #${user.user_id}`}</h3>
          <div className="text-sm text-gray-600 flex gap-2">
            <span>{user.age ? `${user.age} yrs` : 'Unknown Age'}</span>
            <span>&bull;</span>
            <span>{user.gender || 'Unknown Gender'}</span>
          </div>
        </div>
      </div>

      <div className="flex-1">
        <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Occupation</h4>
        <div className="flex items-center gap-2">
          <div className="p-2 bg-indigo-50 rounded-lg text-indigo-600">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="text-gray-800 font-medium capitalize">
            {user.occupation || 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
}
