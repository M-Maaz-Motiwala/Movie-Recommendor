import React, { useEffect, useState } from 'react';
import api from '../services/api';

export default function Recommendations({ items, loading, userId, onRefresh, userInteractions = [] }) {
  const [ratingStates, setRatingStates] = useState({}); // { itemId: { rating: 5, loading: false, success: false } }

  useEffect(() => {
    const nextStates = {};
    userInteractions.forEach(interaction => {
      if (interaction?.item_id != null && interaction?.rating != null) {
        nextStates[interaction.item_id] = {
          rating: interaction.rating,
          loading: false,
          success: true,
        };
      }
    });
    setRatingStates(nextStates);
  }, [userInteractions]);

  const handleRate = async (itemId, rating) => {
    if (!userId) return;
    
    setRatingStates(prev => ({
      ...prev,
      [itemId]: { ...prev[itemId], loading: true }
    }));

    try {
      await api.post('/interactions', {
        user_id: parseInt(userId),
        item_id: parseInt(itemId),
        rating: parseFloat(rating),
        liked: rating >= 4
      });
      
      setRatingStates(prev => ({
        ...prev,
        [itemId]: { loading: false, success: true, rating }
      }));
    } catch (err) {
      console.error("Rating failed", err);
      setRatingStates(prev => ({
        ...prev,
        [itemId]: { ...prev[itemId], loading: false }
      }));
    }
  };

  if (loading) {
    return (
      <div className="glass-card p-12 flex flex-col items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-indigo-600 font-medium">Crunching the numbers...</p>
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="glass-card p-12 flex flex-col items-center justify-center text-gray-400">
        <svg className="w-16 h-16 mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
        </svg>
        <p className="text-lg">No recommendations to display yet.</p>
        <p className="text-sm mt-1">Select a user to begin.</p>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between border-b border-gray-200 pb-2 mb-6">
        <h2 className="text-xl font-bold text-gray-800">Recommended For You</h2>
        <span className="text-xs font-semibold px-2.5 py-1 bg-green-100 text-green-700 rounded-full">Top {items.length} Matches</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {items.map(it => {
          const percentage = it.score ? Math.min(Math.max(Math.round(it.score * 100), 0), 100) : 0;
          const state = ratingStates[it.item_id] || {};
          
          return (
            <div key={it.item_id} className="glass-card-hover bg-white/60 rounded-xl overflow-hidden border border-gray-100 flex flex-col group">
              <div className="h-40 bg-gray-200 relative overflow-hidden flex items-center justify-center">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/80 to-purple-900/80 z-0 transition-transform duration-500 group-hover:scale-110"></div>
                <svg className="w-12 h-12 text-white/30 z-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                
                <div className="absolute top-3 right-3 z-10 flex items-center justify-center w-10 h-10 bg-white/90 rounded-full shadow border-2 border-indigo-500 font-bold text-indigo-700 text-sm">
                  {percentage}
                </div>
              </div>
              
              <div className="p-4 flex-1 flex flex-col">
                <h3 className="font-bold text-gray-900 leading-tight mb-1 line-clamp-2">{it.title}</h3>
                <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-3">Item ID: {it.item_id}</p>
                
                <div className="mt-auto">
                  {state.success ? (
                    <div className="flex items-center justify-center py-2 bg-green-50 text-green-600 rounded-lg text-xs font-bold animate-in zoom-in duration-300">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Rated {state.rating}/5
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 overflow-hidden">
                      {[1, 2, 3, 4, 5].map(num => (
                        <button
                          key={num}
                          onClick={() => handleRate(it.item_id, num)}
                          disabled={state.loading}
                          className="flex-1 py-1.5 bg-gray-50 hover:bg-indigo-600 hover:text-white text-gray-400 rounded transition-all duration-200 text-[10px] font-bold border border-gray-100"
                        >
                          {num}
                        </button>
                      ))}
                    </div>
                  )}
                  
                  <div className="mt-3 pt-2 border-t border-gray-50 flex items-center justify-between">
                    <span className="text-[10px] font-bold text-gray-400 uppercase">Confidence</span>
                    <div className="flex items-center gap-1 text-amber-500">
                      <svg className="w-3 h-3 fill-current" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-xs font-bold">{it.score?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
