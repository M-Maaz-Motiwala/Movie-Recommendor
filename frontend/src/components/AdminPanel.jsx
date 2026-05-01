import React, { useEffect, useState } from 'react'
import api from '../services/api'

export default function AdminPanel({ onUserAdded }) {
  const [stats, setStats] = useState({ users: 0, items: 0, interactions: 0 })
  const [loading, setLoading] = useState(false)
  
  // Form states
  const [newUser, setNewUser] = useState({ name: '', age: '', gender: 'M', occupation: '' })
  const [newMovie, setNewMovie] = useState({ title: '', genres: '' })
  const [activeTab, setActiveTab] = useState('stats')

  const fetchStats = async () => {
    try {
      const res = await api.get('/admin/stats')
      setStats(res.data)
    } catch (e) {
      setStats({ users: 0, items: 0, interactions: 0 })
    }
  }

  useEffect(() => { fetchStats() }, [])

  const seed = async () => {
    setLoading(true)
    await api.post('/admin/seed')
    await fetchStats()
    if (onUserAdded) onUserAdded()
    setLoading(false)
  }

  const retrain = async () => {
    setLoading(true)
    await api.post('/admin/retrain')
    setLoading(false)
  }

  const handleAddUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/users/', {
        ...newUser,
        age: newUser.age ? parseInt(newUser.age) : null
      })
      setNewUser({ name: '', age: '', gender: 'M', occupation: '' })
      await fetchStats()
      if (onUserAdded) onUserAdded()
    } catch (err) {
      console.error("Failed to add user", err)
    }
    setLoading(false)
  }

  const handleAddMovie = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/items/', newMovie)
      setNewMovie({ title: '', genres: '' })
      await fetchStats()
    } catch (err) {
      console.error("Failed to add movie", err)
    }
    setLoading(false)
  }

  return (
    <div className="space-y-4">
      <div className="flex border-b border-gray-100 overflow-x-auto no-scrollbar">
        {['stats', 'add-user', 'add-movie'].map(tab => (
          <button 
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-[11px] uppercase tracking-wider font-bold transition-colors whitespace-nowrap ${activeTab === tab ? 'text-indigo-600 border-b-2 border-indigo-600' : 'text-gray-400 hover:text-gray-600'}`}
          >
            {tab.replace('-', ' ')}
          </button>
        ))}
      </div>

      {activeTab === 'stats' && (
        <div className="space-y-4 animate-in fade-in duration-300">
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-gray-50/50 rounded-lg border border-gray-100 text-center">
              <div className="text-[10px] text-gray-500 uppercase font-bold tracking-tight">Users</div>
              <div className="text-lg font-bold text-gray-800">{stats.users}</div>
            </div>
            <div className="p-3 bg-gray-50/50 rounded-lg border border-gray-100 text-center">
              <div className="text-[10px] text-gray-500 uppercase font-bold tracking-tight">Movies</div>
              <div className="text-lg font-bold text-gray-800">{stats.items}</div>
            </div>
            <div className="p-3 bg-gray-50/50 rounded-lg border border-gray-100 text-center">
              <div className="text-[10px] text-gray-500 uppercase font-bold tracking-tight">Ratings</div>
              <div className="text-lg font-bold text-gray-800">{stats.interactions}</div>
            </div>
          </div>
          {/* <div className="flex flex-wrap gap-2">
            <button onClick={seed} className="flex-1 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 transition-colors shadow-sm uppercase tracking-wide">Seed Data</button>
            <button onClick={retrain} className="flex-1 px-3 py-2 bg-white text-gray-700 border border-gray-200 rounded-lg text-xs font-bold hover:bg-gray-50 transition-colors uppercase tracking-wide">Retrain</button>
          </div> */}
        </div>
      )}

      {activeTab === 'add-user' && (
        <form onSubmit={handleAddUser} className="space-y-3 animate-in slide-in-from-left-2 duration-300">
          <input 
            type="text" 
            placeholder="Name" 
            className="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={newUser.name}
            onChange={e => setNewUser({...newUser, name: e.target.value})}
            required
          />
          <div className="flex gap-2">
            <input 
              type="number" 
              placeholder="Age" 
              className="w-20 px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={newUser.age}
              onChange={e => setNewUser({...newUser, age: e.target.value})}
            />
            <select 
              className="flex-1 px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={newUser.gender}
              onChange={e => setNewUser({...newUser, gender: e.target.value})}
            >
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>
          <input 
            type="text" 
            placeholder="Occupation" 
            className="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={newUser.occupation}
            onChange={e => setNewUser({...newUser, occupation: e.target.value})}
          />
          <button type="submit" disabled={loading} className="w-full py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 transition-colors uppercase tracking-wide">
            {loading ? 'Adding...' : 'Confirm User'}
          </button>
        </form>
      )}

      {activeTab === 'add-movie' && (
        <form onSubmit={handleAddMovie} className="space-y-3 animate-in slide-in-from-right-2 duration-300">
          <input 
            type="text" 
            placeholder="Movie Title" 
            className="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={newMovie.title}
            onChange={e => setNewMovie({...newMovie, title: e.target.value})}
            required
          />
          <input 
            type="text" 
            placeholder="Genres (e.g. Action, Sci-Fi)" 
            className="w-full px-3 py-2 text-sm bg-gray-50 border border-gray-100 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            value={newMovie.genres}
            onChange={e => setNewMovie({...newMovie, genres: e.target.value})}
          />
          <button type="submit" disabled={loading} className="w-full py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 transition-colors uppercase tracking-wide">
            {loading ? 'Adding...' : 'Confirm Movie'}
          </button>
        </form>
      )}
      
      {loading && activeTab === 'stats' && <div className="text-center text-xs text-indigo-600 animate-pulse">Processing...</div>}
    </div>
  )
}
