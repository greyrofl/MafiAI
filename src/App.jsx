import React, { useState, useEffect } from 'react'
import { Plus, Users, Play, Send, Mic, Moon, Sun, Bot, Skull, X, User, Clock, ChevronRight, Shield, Ghost, Zap, Wifi, LogIn, UserPlus, Eye, Ghost as GhostIcon, Sparkles, ArrowRight, Loader2 } from 'lucide-react'

const API_URL = 'http://localhost:5173'

const playerProfiles = {
  1: { id: 1, name: 'Alexey', avatar: 'A', color: 'bg-pink-500', bio: 'Стратег', stats: { games: 47, wins: 23, winrate: 48.9 }, achievements: ['Первая кровь'], joinDate: '2024-01-15' },
  2: { id: 2, name: 'Maria', avatar: 'M', color: 'bg-rose-500', bio: 'Интуитивный', stats: { games: 32, wins: 18, winrate: 56.2 }, achievements: [], joinDate: '2024-02-20' },
  3: { id: 3, name: 'Dmitry', avatar: 'D', color: 'bg-rose-400', bio: 'Честный', stats: { games: 28, wins: 12, winrate: 42.8 }, achievements: [], joinDate: '2024-03-10' },
  4: { id: 4, name: 'Elena', avatar: 'E', color: 'bg-pink-400', bio: 'Упорная', stats: { games: 55, wins: 31, winrate: 56.4 }, achievements: [], joinDate: '2023-11-05' },
  5: { id: 5, name: 'Neural_7', avatar: '7', color: 'bg-pink-600', bio: 'AI v7.2.1', stats: { games: 1250, wins: 687, winrate: 55.0 }, achievements: [], isAI: true, joinDate: '2024-01-01' },
  6: { id: 6, name: 'Neural_3', avatar: '3', color: 'bg-rose-600', bio: 'AI v3.8.4', stats: { games: 890, wins: 445, winrate: 50.0 }, achievements: [], isAI: true, joinDate: '2024-01-01' },
}

const ROLES = {
  mafia: { name: 'Мафия', icon: Ghost, color: 'text-rose-500', bg: 'bg-rose-500/20', description: 'Убивай мирных' },
  villager: { name: 'Мирный', icon: User, color: 'text-pink-500', bg: 'bg-pink-500/20', description: 'Найди мафию' },
  sheriff: { name: 'Шериф', icon: Shield, color: 'text-rose-400', bg: 'bg-rose-400/20', description: 'Арестуй мафию' },
  doctor: { name: 'Доктор', icon: Zap, color: 'text-pink-400', bg: 'bg-pink-400/20', description: 'Спасай мирных' },
}

const BUBBLES = [
  { x: 10, y: 20, size: 300, color: 'bg-pink-500', delay: 0 },
  { x: 80, y: 10, size: 200, color: 'bg-rose-500', delay: 2 },
  { x: 30, y: 70, size: 250, color: 'bg-pink-400', delay: 4 },
  { x: 70, y: 60, size: 180, color: 'bg-rose-400', delay: 1 },
  { x: 50, y: 40, size: 350, color: 'bg-pink-300', delay: 3 },
  { x: 20, y: 85, size: 150, color: 'bg-rose-300', delay: 5 },
]

function BubbleBackground() {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {BUBBLES.map((bubble, i) => (
        <div key={i} className={`absolute rounded-full ${bubble.color} blur-3xl opacity-30 animate-float`} style={{ left: `${bubble.x}%`, top: `${bubble.y}%`, width: bubble.size, height: bubble.size, animationDelay: `${bubble.delay}s` }} />
      ))}
    </div>
  )
}

function ThemeToggle({ theme, setTheme }) {
  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} className={`p-3 rounded-full transition-all hover:scale-110 active:scale-95 z-10 ${theme === 'dark' ? 'bg-white/10 text-rose-300 hover:bg-white/20' : 'bg-white/80 text-slate-600 hover:bg-white'}`}>
      {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  )
}

async function apiCall(endpoint, options = {}) {
  const token = localStorage.getItem('token')
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  
  const apiEndpoint = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`
  const method = (options || {}).method || 'GET'
  console.log(`API call: ${API_URL}${apiEndpoint} [${method}]`)
  
  const fetchOptions = { headers }
  if (method !== 'GET') {
    fetchOptions.method = method
    fetchOptions.body = options.body
  }
  
  const response = await fetch(`${API_URL}${apiEndpoint}`, fetchOptions)
  console.log(`Response: ${response.status}`, response.statusText)
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: `Error ${response.status}` }))
    console.error('API Error:', error)
    throw new Error(error.detail || 'Request failed')
  }
  return response.json()
}

function RoleReveal({ role, onComplete }) {
  const [showRole, setShowRole] = useState(false)
  const roleData = ROLES[role] || ROLES.citizen
  const Icon = roleData.icon

  useEffect(() => {
    const showTimer = setTimeout(() => setShowRole(true), 500)
    const closeTimer = setTimeout(() => onComplete(), 4000)
    return () => { clearTimeout(showTimer); clearTimeout(closeTimer) }
  }, [onComplete])

  const handleClick = () => {
    setShowRole(true)
    setTimeout(() => onComplete(), 500)
  }

  return (
    <div onClick={handleClick} className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 backdrop-blur-md cursor-pointer">
      <div className={`text-center ${showRole ? 'animate-scale-in' : 'animate-fade-in'}`}>
        {!showRole ? (
          <div className="w-40 h-52 bg-slate-800 rounded-[32px] flex items-center justify-center border border-slate-700">
            <div className="text-6xl font-bold text-rose-500 animate-pulse">?</div>
          </div>
        ) : (
          <div className={`w-72 h-96 ${roleData.bg} rounded-[40px] flex flex-col items-center justify-center gap-6 border-4 ${roleData.color.replace('text-', 'border-')} animate-scale-in p-6`}>
            <div className={`p-8 rounded-full ${roleData.bg}`}>
              <Icon className={`w-20 h-20 ${roleData.color}`} />
            </div>
            <div className="text-center">
              <div className="text-sm text-slate-400 mb-1 uppercase tracking-wider">Ваша роль</div>
              <div className={`text-3xl font-bold ${roleData.color}`}>{roleData.name}</div>
              <p className="text-sm text-slate-500 mt-3 max-w-[220px]">{roleData.description}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ProfileModal({ player, theme, onClose }) {
  const p = playerProfiles[player.id] || { ...player, color: 'bg-pink-500', stats: { games: 0, wins: 0, winrate: 0 }, achievements: [] }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className={`w-full max-w-sm rounded-[32px] overflow-hidden ${theme === 'dark' ? 'bg-slate-900' : 'bg-white'} border ${theme === 'dark' ? 'border-slate-800' : 'border-slate-100'}`} onClick={e => e.stopPropagation()}>
        <div className={`h-24 ${p.color} relative`}>
          <button onClick={onClose} className="absolute top-3 right-3 p-2 rounded-full bg-black/20 text-white/80 hover:bg-black/40 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <div className="px-6 pb-6 -mt-12">
          <div className={`w-20 h-20 rounded-full ${p.color} flex items-center justify-center text-2xl font-bold text-white border-4 ${theme === 'dark' ? 'border-slate-900' : 'border-white'}`}>
            {p.avatar || p.name?.[0] || '?'}
          </div>
          <div className="mt-4">
            <div className="flex items-center gap-2">
              <h2 className={`text-xl font-semibold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>{p.name}</h2>
              {p.isAI && <span className="px-2 py-0.5 bg-rose-500/20 text-rose-500 text-xs rounded-full">AI</span>}
            </div>
            <p className={`mt-1 text-sm ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>{p.bio || 'Игрок'}</p>
          </div>
          <div className={`mt-5 grid grid-cols-3 gap-2 p-4 rounded-[20px] ${theme === 'dark' ? 'bg-slate-800' : 'bg-slate-50'}`}>
            <div className="text-center">
              <div className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>{p.stats.games}</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}`}>Игр</div>
            </div>
            <div className="text-center">
              <div className={`text-xl font-bold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>{p.stats.wins}</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}`}>Побед</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold text-rose-500">{p.stats.winrate}%</div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}`}>Winrate</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function AuthScreen({ onLogin, theme }) {
  const [mode, setMode] = useState('login') // login, register, verify
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [verifyCode, setVerifyCode] = useState('')
  const [pendingEmail, setPendingEmail] = useState('')
  const [sentCode, setSentCode] = useState('')

  const bg = theme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'
  const cardBg = theme === 'dark' ? 'bg-slate-900' : 'bg-white'
  const border = theme === 'dark' ? 'border-slate-800' : 'border-slate-200'
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = theme === 'dark' ? 'text-slate-400' : 'text-slate-500'
  const inputBg = theme === 'dark' ? 'bg-slate-800' : 'bg-slate-50'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    
    try {
      if (mode === 'register') {
        const res = await apiCall('/auth/register', {
          method: 'POST',
          body: JSON.stringify({ email, password, username: name })
        })
        console.log('Register response:', res)
        setPendingEmail(email)
        setSentCode(res.code || res.code || '')
        setMode('verify')
      } else if (mode === 'verify') {
        await apiCall('/auth/verify', {
          method: 'POST',
          body: JSON.stringify({ email: pendingEmail, code: verifyCode })
        })
        setMode('login')
        setError('Аккаунт подтверждён! Войдите.')
      } else {
        const data = await apiCall('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email, password })
        })
        localStorage.setItem('token', data.access_token)
        const userData = await apiCall('/auth/me')
        onLogin({ name: userData.username, email: userData.email, avatar: userData.username?.[0]?.toUpperCase() || 'P', color: 'bg-pink-500' })
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className={`min-h-screen ${bg} flex items-center justify-center p-4 relative`}>
      <BubbleBackground />
      <div className={`relative z-10 w-full max-w-sm`}>
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-500 mb-4">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h1 className={`text-3xl font-bold ${textPrimary}`}>MafiAI</h1>
          <p className={`text-sm ${textSecondary} mt-1`}>
            {mode === 'verify' ? 'Подтверди email' : mode === 'register' ? 'Создай аккаунт' : 'Войди в игру'}
          </p>
        </div>
        <form onSubmit={handleSubmit} className={`${cardBg} rounded-[32px] p-6 border ${border}`}>
          {error && <div className={`mb-4 p-3 text-sm rounded-xl ${error.includes('успех') || error.includes('подтверждён') ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'}`}>{error}</div>}
          {mode === 'verify' ? (
            <div className="mb-4">
              {sentCode && (
                <div className="mb-4 p-4 bg-rose-500/20 rounded-xl text-center">
                  <p className={`text-sm ${textSecondary} mb-1`}>Код из email (если не пришёл):</p>
                  <div className={`text-3xl font-bold text-rose-500 tracking-widest`}>{sentCode}</div>
                </div>
              )}
              <label className={`block text-sm font-medium ${textSecondary} mb-2`}>Введите код из email</label>
              <input type="text" value={verifyCode} onChange={(e) => setVerifyCode(e.target.value)} placeholder="123456" className={`w-full px-4 py-3 rounded-xl ${inputBg} ${textPrimary} outline-none focus:ring-2 focus:ring-rose-500 transition-all text-center text-2xl tracking-widest`} maxLength={6} />
            </div>
          ) : (
            <>
              {mode === 'register' && (
                <div className="mb-4">
                  <label className={`block text-sm font-medium ${textSecondary} mb-2`}>Имя</label>
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Как тебя зовут?" className={`w-full px-4 py-3 rounded-xl ${inputBg} ${textPrimary} outline-none focus:ring-2 focus:ring-rose-500 transition-all`} />
                </div>
              )}
              <div className="mb-4">
                <label className={`block text-sm font-medium ${textSecondary} mb-2`}>Email</label>
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="example@mail.ru" className={`w-full px-4 py-3 rounded-xl ${inputBg} ${textPrimary} outline-none focus:ring-2 focus:ring-rose-500 transition-all`} />
              </div>
              <div className="mb-6">
                <label className={`block text-sm font-medium ${textSecondary} mb-2`}>Пароль</label>
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className={`w-full px-4 py-3 rounded-xl ${inputBg} ${textPrimary} outline-none focus:ring-2 focus:ring-rose-500 transition-all`} />
              </div>
            </>
          )}
          <button type="submit" disabled={isLoading} className="w-full py-3.5 bg-rose-500 text-white rounded-xl font-medium hover:bg-rose-600 active:scale-[0.98] transition-all flex items-center justify-center gap-2">
            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : mode === 'verify' ? <Shield className="w-5 h-5" /> : mode === 'register' ? <UserPlus className="w-5 h-5" /> : <LogIn className="w-5 h-5" />}
            {isLoading ? 'Подождите...' : mode === 'verify' ? 'Подтвердить' : mode === 'register' ? 'Создать аккаунт' : 'Войти'}
          </button>
          {mode === 'verify' && (
            <button type="button" onClick={() => setMode('register')} className="w-full py-3 mt-3 text-rose-500 hover:text-rose-400 text-sm font-medium transition-colors">
              Назад
            </button>
          )}
          {mode !== 'verify' && (
            <>
              <button type="button" onClick={() => onLogin({ name: 'Гость', email: 'guest@local', avatar: 'Г', color: 'bg-slate-500', isGuest: true })} className="w-full py-3 mt-3 text-rose-500 hover:text-rose-400 text-sm font-medium transition-colors">
                Продолжить как гость
              </button>
              <div className="mt-6 text-center">
                <button type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')} className={`text-sm ${textSecondary} hover:text-rose-500 transition-colors`}>
                  {mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
                </button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}

function WelcomeScreen({ gameState, setGameState, theme, setTheme, user }) {
  const [joinId, setJoinId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [rooms, setRooms] = useState([])
  const [error, setError] = useState('')

  const bg = theme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'
  const cardBg = theme === 'dark' ? 'bg-slate-900' : 'bg-white'
  const border = theme === 'dark' ? 'border-slate-800' : 'border-slate-200'
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = theme === 'dark' ? 'text-slate-400' : 'text-slate-500'

  useEffect(() => {
    loadRooms()
    const interval = setInterval(loadRooms, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadRooms = async () => {
    try {
      const data = await apiCall('/rooms')
      setRooms(data)
    } catch (e) {
      console.error('Failed to load rooms:', e)
    }
  }

  const handleCreateRoom = async () => {
    if (!user || user.isGuest || !user.name) {
      setError('Войдите в аккаунт для создания комнаты')
      return
    }
    setIsLoading(true)
    setError('')
    try {
      const room = await apiCall('/rooms', {
        method: 'POST',
        body: JSON.stringify({
          name: 'Комната ' + (user?.name || 'Player'),
          is_public: true,
          room_type: 'open',
          max_players: 7,
          ai_count: 3,
          game_type: 'standard',
          time_limit: 15
        })
      })
      setGameState({ ...gameState, currentScreen: 'lobby', roomId: room.id, roomCode: room.room_code, players: [], isHost: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleJoinRoom = async () => {
    if (!user || user.isGuest || !user.name) {
      setError('Войдите в аккаунт для входа в комнату')
      return
    }
    if (!joinId.trim()) return
    setIsLoading(true)
    setError('')
    try {
      const room = await apiCall(`/rooms/code/${joinId.toUpperCase()}`)
      setGameState({ ...gameState, currentScreen: 'lobby', roomId: room.id, roomCode: room.room_code, players: room.players, isHost: false })
    } catch (err) {
      setError('Комната не найдена')
    } finally {
      setIsLoading(false)
    }
  }

  const features = [
    { icon: Bot, title: 'AI Агенты', desc: 'Боты на YandexGPT' },
    { icon: GhostIcon, title: 'Neural Memory', desc: 'ИИ запоминает' },
    { icon: Eye, title: 'Admin View', desc: 'Видишь мысли ботов' },
  ]

  return (
    <div className={`min-h-screen ${bg} overflow-hidden relative`}>
      <BubbleBackground />
      <div className="absolute top-6 right-6 z-10 flex items-center gap-3">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${cardBg} border ${border}`}>
          <div className="w-6 h-6 rounded-full bg-pink-500 flex items-center justify-center text-xs font-medium text-white">{user?.avatar || 'P'}</div>
          <span className={`text-sm ${textPrimary}`}>{user?.name || 'Player'}</span>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
      <div className="relative z-10 max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-rose-500 mb-4 shadow-lg shadow-rose-500/30">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h1 className={`text-4xl font-bold ${textPrimary} mb-2`}>MafiAI</h1>
          <p className={`text-lg ${textSecondary}`}>Играй с AI-агентами нового поколения</p>
        </div>

        {error && <div className="mb-4 p-3 bg-red-500/20 text-red-500 text-sm rounded-xl text-center">{error}</div>}

        <div className="grid grid-cols-2 gap-4 mb-10">
          <button onClick={handleCreateRoom} disabled={isLoading} className="group p-6 rounded-[28px] bg-rose-500 text-white hover:scale-[1.02] active:scale-[0.98] transition-all shadow-lg shadow-rose-500/20 disabled:opacity-50">
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">{isLoading ? <Loader2 className="w-6 h-6 animate-spin" /> : <Plus className="w-6 h-6" />}</div>
              <div className="text-center">
                <div className="font-semibold">Создать комнату</div>
                <div className="text-xs text-white/70">Новая игра</div>
              </div>
            </div>
          </button>
          <div className={`${cardBg} p-6 rounded-[28px] border ${border} flex flex-col gap-3`}>
            <div className="flex items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-rose-500/20 flex items-center justify-center"><Users className="w-5 h-5 text-rose-500" /></div>
              <span className={`font-medium ${textPrimary}`}>Присоединиться</span>
            </div>
            <input type="text" placeholder="ID комнаты" value={joinId} onChange={(e) => setJoinId(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleJoinRoom()} className={`w-full px-4 py-2.5 rounded-xl ${theme === 'dark' ? 'bg-slate-800 text-white' : 'bg-slate-50 text-slate-900'} outline-none focus:ring-2 focus:ring-rose-500 transition-all text-sm`} />
            <button onClick={handleJoinRoom} disabled={isLoading || !joinId.trim()} className="w-full py-2.5 bg-rose-500 text-white rounded-xl font-medium hover:bg-rose-600 active:scale-[0.98] transition-all text-sm disabled:opacity-50">Войти</button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3 mb-8">
          {features.map((f, i) => (
            <div key={i} className={`${cardBg} p-4 rounded-[20px] border ${border} text-center`}>
              <div className="w-10 h-10 rounded-xl bg-rose-500/20 flex items-center justify-center mx-auto mb-2"><f.icon className="w-5 h-5 text-rose-500" /></div>
              <div className={`text-sm font-medium ${textPrimary}`}>{f.title}</div>
              <div className={`text-xs ${textSecondary}`}>{f.desc}</div>
            </div>
          ))}
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className={`text-base font-medium ${textPrimary}`}>Комнаты онлайн</h2>
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className={`text-sm ${textSecondary}`}>{rooms.length} активных</span>
            </div>
          </div>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {rooms.length === 0 ? (
              <div className={`${cardBg} p-4 rounded-[20px] border ${border} text-center w-full`}>
                <p className={`text-sm ${textSecondary}`}>Нет доступных комнат</p>
              </div>
            ) : (
              rooms.map((room) => (
                <button key={room.id} onClick={() => { setJoinId(room.room_code); handleJoinRoom() }} className={`${cardBg} p-4 rounded-[20px] border ${border} min-w-[160px] hover:scale-[1.02] transition-all cursor-pointer text-left`}>
                  <div className="flex items-center justify-between mb-1">
                    <div className={`font-semibold ${textPrimary}`}>{room.room_code}</div>
                    <div className="px-2 py-0.5 bg-emerald-500/20 text-emerald-500 text-xs rounded-full">{room.player_count}/{room.max_players}</div>
                  </div>
                  <div className={`text-xs ${textSecondary}`}>{room.name || 'Комната'}</div>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="mt-10 text-center">
          <p className={`text-xs ${textSecondary}`}>MafiAI © 2026 · TulaHack</p>
        </div>
      </div>
    </div>
  )
}

function LobbyScreen({ gameState, setGameState, theme, setTheme, user }) {
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [showRoleReveal, setShowRoleReveal] = useState(false)
  const [myRole, setMyRole] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [players, setPlayers] = useState(gameState.players || [])

  const bg = theme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'
  const cardBg = theme === 'dark' ? 'bg-slate-900' : 'bg-white'
  const border = theme === 'dark' ? 'border-slate-800' : 'border-slate-200'
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = theme === 'dark' ? 'text-slate-400' : 'text-slate-500'

  useEffect(() => {
    if (gameState.roomId) loadRoom()
    const interval = setInterval(loadRoom, 3000)
    return () => clearInterval(interval)
  }, [gameState.roomId])

  const loadRoom = async () => {
    try {
      const room = await apiCall(`/rooms/${gameState.roomId}`)
      setPlayers(room.players || [])
      if (room.phase !== 'lobby' && !showRoleReveal) {
        setGameState({ ...gameState, phase: room.phase, day_number: room.day_number })
      }
    } catch (e) {
      console.error('Failed to load room:', e)
    }
  }

  const handleStartGame = async () => {
    setIsLoading(true)
    try {
      const room = await apiCall(`/rooms/${gameState.roomId}/start`, { method: 'POST' })
      // Find current user's role from room data
      const me = room.players?.find(p => !p.is_ai && p.is_host)
      if (me) {
        setMyRole(me.role || 'citizen')
      }
      setGameState({ ...gameState, phase: room.phase, day_number: room.day_number, players: room.players })
      setShowRoleReveal(true)
      setTimeout(() => setIsLoading(false), 500)
    } catch (err) {
      alert(err.message)
      setIsLoading(false)
    }
  }

  const handleAddAI = async () => {
    try {
      await apiCall(`/rooms/${gameState.roomId}/add-ai`, {
        method: 'POST',
        body: JSON.stringify({ ai_count: 1 })
      })
      loadRoom()
    } catch (e) {
      console.error(e)
    }
  }

  const handleRoleRevealed = () => {
    setShowRoleReveal(false)
    setGameState({ ...gameState, currentScreen: 'game' })
  }

  return (
    <div className={`min-h-screen ${bg} p-6 relative`}>
      <BubbleBackground />
      <div className="absolute top-6 right-6 z-10 flex items-center gap-3">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${cardBg} border ${border}`}>
          <div className="w-6 h-6 rounded-full bg-pink-500 flex items-center justify-center text-xs font-medium text-white">{user?.avatar || 'P'}</div>
          <span className={`text-sm ${textPrimary}`}>{user?.name || 'Player'}</span>
        </div>
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>
      <div className="max-w-4xl mx-auto relative z-10 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-2xl font-bold ${textPrimary}`}>Комната {gameState.roomCode || gameState.roomId}</h1>
            <p className={`text-sm ${textSecondary}`}>Ожидание игроков... ({players.length})</p>
          </div>
          <button onClick={() => setGameState({ ...gameState, currentScreen: 'welcome' })} className={`px-5 py-2.5 ${cardBg} rounded-full border ${border} ${textPrimary} hover:scale-105 active:scale-95 transition-all text-sm font-medium`}>
            Назад
          </button>
        </div>
        <div className="grid grid-cols-4 gap-3">
          {players.map((player, i) => (
            <button key={player.id || i} onClick={() => setSelectedPlayer(player)} className={`${cardBg} p-4 rounded-[24px] border ${border} hover:scale-[1.02] active:scale-[0.98] transition-all flex flex-col items-center gap-2`}>
              <div className={`w-12 h-12 rounded-full ${player.is_ai ? 'bg-pink-600' : 'bg-pink-500'} flex items-center justify-center text-lg font-medium text-white`}>{player.name?.[0] || '?'}</div>
              <div className={`text-sm font-medium ${textPrimary}`}>{player.name}</div>
              {player.is_ai && <span className="text-xs text-rose-500">AI</span>}
              {player.is_host && <span className="text-xs text-amber-500">Хост</span>}
            </button>
          ))}
          {gameState.isHost && players.length < 10 && (
            <button onClick={handleAddAI} className={`${cardBg} p-4 rounded-[24px] border ${border} border-dashed hover:scale-[1.02] transition-all flex flex-col items-center gap-2`}>
              <div className="w-12 h-12 rounded-full bg-slate-700 flex items-center justify-center text-2xl font-medium text-slate-500">+</div>
              <div className={`text-sm ${textSecondary}`}>Добавить AI</div>
            </button>
          )}
        </div>
        {gameState.isHost && (
          <div className="flex justify-center pt-2">
            <button onClick={handleStartGame} disabled={isLoading || players.length < 4} className="fixed bottom-8 right-8 bg-rose-500 text-white px-6 py-3 rounded-full shadow-lg shadow-rose-500/30 hover:scale-105 active:scale-95 transition-all flex items-center gap-2 font-medium disabled:opacity-50">
              <Play className="w-5 h-5" />
              {isLoading ? 'Запуск...' : 'Начать игру'}
            </button>
          </div>
        )}
      </div>
      {selectedPlayer && <ProfileModal player={selectedPlayer} theme={theme} onClose={() => setSelectedPlayer(null)} />}
      {showRoleReveal && myRole && <RoleReveal role={myRole} onComplete={handleRoleRevealed} />}
    </div>
  )
}

function GameScreen({ gameState, setGameState, theme, setTheme, user }) {
  const [newMessage, setNewMessage] = useState('')
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const [messages, setMessages] = useState([])
  const [memory, setMemory] = useState([])
  const [votes, setVotes] = useState({})
  const isNight = gameState.phase === 'night'

  useEffect(() => {
    if (gameState.roomId) {
      loadMessages()
      loadMemory()
      const interval = setInterval(() => { loadMessages(); loadRoom(); }, 2000)
      return () => clearInterval(interval)
    }
  }, [gameState.roomId])

  const loadRoom = async () => {
    try {
      const room = await apiCall(`/rooms/${gameState.roomId}`)
      setGameState({ ...gameState, phase: room.phase, day_number: room.day_number, players: room.players })
    } catch (e) { console.error(e) }
  }

  const loadMessages = async () => {
    try {
      const data = await apiCall(`/rooms/${gameState.roomId}/messages`)
      setMessages(data)
    } catch (e) { console.error(e) }
  }

  const loadMemory = async () => {
    try {
      const data = await apiCall(`/rooms/${gameState.roomId}/memory`)
      setMemory(data)
    } catch (e) { console.error(e) }
  }

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return
    try {
      await apiCall(`/rooms/${gameState.roomId}/messages`, {
        method: 'POST',
        body: JSON.stringify({ text: newMessage })
      })
      setNewMessage('')
      loadMessages()
    } catch (e) { console.error(e) }
  }

  const handleVote = async (targetId) => {
    try {
      await apiCall(`/rooms/${gameState.roomId}/vote`, {
        method: 'POST',
        body: JSON.stringify({ targetId })
      })
      loadRoom()
    } catch (e) { console.error(e) }
  }

  const togglePhase = async () => {
    try {
      await apiCall(`/rooms/${gameState.roomId}/phase`, { method: 'POST' })
      loadRoom()
    } catch (e) { console.error(e) }
  }

  const currentTheme = isNight ? 'dark' : theme
  const bg = currentTheme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'
  const headerBg = currentTheme === 'dark' ? 'bg-slate-900/80' : 'bg-white/80'
  const cardBg = currentTheme === 'dark' ? 'bg-slate-900' : 'bg-white'
  const border = currentTheme === 'dark' ? 'border-slate-800' : 'border-slate-200'
  const textPrimary = currentTheme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = currentTheme === 'dark' ? 'text-slate-400' : 'text-slate-500'
  const inputBg = currentTheme === 'dark' ? 'bg-slate-800' : 'bg-slate-50'

  const players = gameState.players || []

  return (
    <div className={`min-h-screen ${bg} transition-colors duration-700`}>
      <BubbleBackground />
      <div className={`${headerBg} px-6 py-3 flex items-center justify-between border-b ${border} backdrop-blur-sm relative z-10`}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-rose-500 flex items-center justify-center"><Shield className="w-5 h-5 text-white" /></div>
          <span className={`font-bold ${textPrimary}`}>MafiAI</span>
          <span className={`text-sm ${textSecondary}`}>{gameState.roomCode || gameState.roomId}</span>
          <span className={`text-sm px-2 py-0.5 rounded ${isNight ? 'bg-slate-800 text-amber-400' : 'bg-rose-500 text-white'}`}>
            {isNight ? 'Ночь' : 'День'} {gameState.day_number || 1}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle theme={theme} setTheme={setTheme} />
          <button onClick={async () => { try { await apiCall(`/rooms/${gameState.roomId}/ai-turn`, { method: 'POST' }); loadMessages(); } catch(e) { console.error(e) } }} className={`flex items-center gap-2 px-3 py-2 rounded-full text-sm font-medium bg-pink-600 text-white hover:scale-105 active:scale-95 transition-all`}>
            <Bot className="w-4 h-4" />ИИ
          </button>
          <button onClick={togglePhase} className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium ${isNight ? 'bg-slate-800 text-amber-400' : 'bg-rose-500 text-white'} hover:scale-105 active:scale-95 transition-all`}>
            {isNight ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            {isNight ? 'Ночь' : 'День'}
          </button>
        </div>
      </div>
      <div className="grid grid-cols-5 h-[calc(100vh-57px)] relative z-10">
        <div className="p-3 space-y-2 overflow-y-auto">
          <h2 className={`text-xs font-medium ${textSecondary} mb-2`}>Игроки ({players.filter(p => p.is_alive).length}/{players.length})</h2>
          {players.map((player, i) => (
            <button key={player.id || i} onClick={() => setSelectedPlayer(player)} className={`w-full p-3 rounded-[20px] ${player.is_alive ? cardBg : (currentTheme === 'dark' ? 'bg-slate-900/50' : 'bg-slate-100')} ${border} flex items-center gap-2 hover:scale-[1.01] active:scale-[0.99] transition-all`}>
              <div className={`w-8 h-8 rounded-full ${player.is_ai ? 'bg-pink-600' : 'bg-pink-500'} flex items-center justify-center text-xs font-medium ${player.is_alive ? 'text-white' : 'text-slate-400'}`}>{player.name?.[0] || '?'}</div>
              <div className="flex-1 text-left">
                <div className={`text-sm font-medium ${textPrimary} ${!player.is_alive && 'line-through opacity-50'}`}>{player.name}</div>
                {player.is_ai && <span className="text-xs text-rose-500">AI</span>}
                {!player.is_alive && <span className="text-xs text-slate-500">Мёртв</span>}
              </div>
            </button>
          ))}
        </div>
        <div className={`col-span-2 p-3 flex flex-col ${currentTheme === 'dark' ? 'bg-slate-900/50' : 'bg-white/50'} border-x ${border}`}>
          <h2 className={`text-xs font-medium ${textSecondary} mb-2`}>Чат</h2>
          <div className="flex-1 overflow-y-auto space-y-3 pb-3">
            {messages.map((msg, i) => (
              <div key={msg.id || i}>
                <div className={`text-sm font-semibold ${textPrimary} flex items-center gap-1.5`}>{msg.player_name}{msg.is_ai && <Bot className="w-3 h-3 text-rose-500" />}</div>
                <p className={`text-sm ${textSecondary}`}>{msg.text}</p>
              </div>
            ))}
          </div>
          <div className={`mt-2 flex items-center gap-2 ${inputBg} p-1.5 rounded-full`}>
            <button className={`p-2 rounded-full ${currentTheme === 'dark' ? 'hover:bg-slate-700' : 'hover:bg-slate-200'} transition-colors`}><Mic className={`w-4 h-4 ${textSecondary}`} /></button>
            <input type="text" value={newMessage} onChange={(e) => setNewMessage(e.target.value)} onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()} placeholder="Сообщение..." className={`flex-1 bg-transparent outline-none text-sm ${textPrimary} placeholder:text-slate-500`} />
            <button onClick={handleSendMessage} className="p-2 bg-rose-500 text-white rounded-full hover:bg-rose-600 transition-colors"><Send className="w-4 h-4" /></button>
          </div>
        </div>
        <div className="col-span-2 p-3">
          <h2 className={`text-xs font-medium ${textSecondary} mb-2`}>Neural Memory</h2>
          <div className="space-y-2">
            {memory.length === 0 ? (
              <div className={`p-3 rounded-[20px] ${cardBg} border ${border}`}>
                <p className={`text-sm ${textSecondary}`}>Пока ничего не произошло</p>
              </div>
            ) : (
              memory.map((m, i) => (
                <div key={i} className={`p-3 rounded-[20px] ${cardBg} border ${border}`}>
                  <div className={`text-xs font-medium mb-1 ${isNight ? 'text-rose-400' : 'text-rose-500'}`}>День {m.day}</div>
                  <p className={`text-sm ${textSecondary}`}>{m.summary}</p>
                </div>
              ))
            )}
          </div>
          <div className="mt-4">
            <h3 className={`text-xs font-medium ${textSecondary} mb-2`}>Голосование</h3>
            <div className="space-y-1.5">
              {players.filter(p => p.is_alive).map((player) => (
                <button key={player.id} onClick={() => handleVote(player.id)} className={`w-full p-2.5 rounded-[16px] ${cardBg} hover:${currentTheme === 'dark' ? 'bg-slate-800' : 'bg-slate-50'} border ${border} flex items-center justify-between transition-all hover:scale-[1.01]`}>
                  <div className="flex items-center gap-2">
                    <div className={`w-6 h-6 rounded-full ${player.is_ai ? 'bg-pink-600' : 'bg-pink-500'} flex items-center justify-center text-xs font-medium text-white`}>{player.name?.[0] || '?'}</div>
                    <span className={`text-sm font-medium ${textPrimary}`}>{player.name}</span>
                  </div>
                  <span className={`text-xs ${textSecondary}`}>{votes[player.id] || 0}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      {selectedPlayer && <ProfileModal player={selectedPlayer} theme={theme} onClose={() => setSelectedPlayer(null)} />}
    </div>
  )
}

export default function App() {
  const [gameState, setGameState] = useState({ currentScreen: 'login', roomId: null, roomCode: null, phase: 'day', day_number: 1, players: [] })
  const [theme, setTheme] = useState('dark')
  const [user, setUser] = useState(null)

  useEffect(() => { document.documentElement.classList.toggle('dark', theme === 'dark') }, [theme])

  const handleLogin = (userData) => {
    setUser(userData)
    setGameState({ ...gameState, currentScreen: 'welcome' })
  }

  return (
    <div className="font-sans antialiased">
      <style>{`
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        .animate-float { animation: float 8s ease-in-out infinite; }
        @keyframes fade-in { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
        .animate-fade-in { animation: fade-in 0.4s ease-out; }
        @keyframes scale-in { from { opacity: 0; transform: scale(0.8); } to { opacity: 1; transform: scale(1); } }
        .animate-scale-in { animation: scale-in 0.5s ease-out; }
      `}</style>
      {gameState.currentScreen === 'login' && <AuthScreen onLogin={handleLogin} theme={theme} />}
      {gameState.currentScreen === 'welcome' && <WelcomeScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} user={user} />}
      {gameState.currentScreen === 'lobby' && <LobbyScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} user={user} />}
      {gameState.currentScreen === 'game' && <GameScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} user={user} />}
    </div>
  )
}