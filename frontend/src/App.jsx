import React, { useEffect, useState } from 'react';
import UserSelector from './components/UserSelector';
import UserProfile from './components/UserProfile';
import Recommendations from './components/Recommendations';
import AlgorithmInsights from './components/AlgorithmInsights';
import AdminPanel from './components/AdminPanel';
import api from './services/api';

export default function App() {
  const [users, setUsers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [recs, setRecs] = useState([]);
  const [interactionCount, setInteractionCount] = useState(null);
  const [userInteractions, setUserInteractions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.get('/users').then(r => setUsers(r.data)).catch(() => setUsers([]));
  }, []);

  const fetchRecs = async (userId) => {
    if (!userId) return;
    setLoading(true);
    try {
      const res = await api.get(`/recommend/${userId}`);
      setRecs(res.data.recommendations);
      setInteractionCount(res.data.interaction_count || 0);
    } catch (e) {
      setRecs([]);
      setInteractionCount(0);
    }
    setLoading(false);
  };

  const fetchUserInteractions = async (userId) => {
    if (!userId) {
      setUserInteractions([]);
      return;
    }
    try {
      const res = await api.get('/interactions');
      const interactions = res.data.filter(item => item.user_id === userId && item.rating != null);
      setUserInteractions(interactions);
    } catch (e) {
      setUserInteractions([]);
    }
  };

  const refreshUsers = () => {
    api.get('/users').then(r => setUsers(r.data)).catch(() => setUsers([]));
  };

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Top Navigation */}
      <header className="max-w-7xl mx-auto mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-600 rounded-lg shadow-lg flex items-center justify-center text-white">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
            </svg>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 tracking-tight">Movie Recommendaor</h1>
        </div>
        <div className="text-sm font-medium text-gray-500">v2.0 Beta</div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Sidebar - Context Area */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="h-auto">
            <UserSelector 
              users={users} 
              selected={selected} 
              onSelect={(u) => {
                setSelected(u);
                setRecs([]); // clear previous recs on user change
                setInteractionCount(null);
                fetchUserInteractions(u?.user_id);
              }} 
              onGet={() => fetchRecs(selected?.user_id)} 
            />
          </div>
          <div className="h-auto">
            <UserProfile user={selected} />
          </div>
          <div className="h-auto">
             <div className="glass-card p-6">
               <h2 className="text-lg font-bold text-gray-800 mb-2 border-b border-gray-200 pb-2">Admin Tools</h2>
               <AdminPanel onUserAdded={refreshUsers} />
             </div>
          </div>
        </div>

        {/* Right Main Content Area */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <Recommendations 
            items={recs} 
            loading={loading} 
            userId={selected?.user_id}
            userInteractions={userInteractions}
            onRefresh={() => {
              fetchUserInteractions(selected?.user_id);
              fetchRecs(selected?.user_id);
            }}
          />
          
          <AlgorithmInsights interactionCount={interactionCount} />
        </div>
      </main>
    </div>
  );
}
