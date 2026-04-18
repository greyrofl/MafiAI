import React, { useState, useEffect } from 'react'
import { Plus, Users, Play, Send, Mic, Moon, Sun, Bot, Skull, Settings, X, User, Trophy, Target, Clock, ChevronRight } from 'lucide-react'

const playerProfiles = {
  1: {
    id: 1,
    name: 'Alexey',
    avatar: 'A',
    color: 'bg-indigo-500',
    bio: 'Стратег с аналитическим складом ума',
    stats: { games: 47, wins: 23, winrate: 48.9 },
    achievements: ['Первая кровь', 'Мафиози недели', 'Мастер детектив'],
    joinDate: '2024-01-15',
  },
  2: {
    id: 2,
    name: 'Maria',
    avatar: 'M',
    color: 'bg-rose-500',
    bio: 'Интуитивный игрок, доверяю чувствам',
    stats: { games: 32, wins: 18, winrate: 56.2 },
    achievements: ['Быстрый удар', 'Последний герой'],
    joinDate: '2024-02-20',
  },
  3: {
    id: 3,
    name: 'Dmitry',
    avatar: 'D',
    color: 'bg-emerald-500',
    bio: 'Играю честно и открыто',
    stats: { games: 28, wins: 12, winrate: 42.8 },
    achievements: ['Справедливый суд'],
    joinDate: '2024-03-10',
  },
  4: {
    id: 4,
    name: 'Elena',
    avatar: 'E',
    color: 'bg-amber-500',
    bio: 'Никогда не сдаюсь до последнего',
    stats: { games: 55, wins: 31, winrate: 56.4 },
    achievements: ['Стальные нервы', 'Мафиози месяца', 'Хладнокровный'],
    joinDate: '2023-11-05',
  },
  5: {
    id: 5,
    name: 'Sergey',
    avatar: 'S',
    color: 'bg-cyan-500',
    bio: 'Новичок, учусь на ошибках',
    stats: { games: 8, wins: 2, winrate: 25.0 },
    achievements: [],
    joinDate: '2024-06-01',
  },
  6: {
    id: 6,
    name: 'Neural_7',
    avatar: '7',
    color: 'bg-violet-500',
    bio: 'AI-агент v7.2.1 | Обучение: 10M партий',
    stats: { games: 1250, wins: 687, winrate: 55.0 },
    achievements: ['Суперкомпьютер', 'Нечеловеческая интуиция'],
    isAI: true,
    joinDate: '2024-01-01',
  },
  7: {
    id: 7,
    name: 'Neural_3',
    avatar: '3',
    color: 'bg-purple-500',
    bio: 'AI-агент v3.8.4 | Обучение: 5M партий',
    stats: { games: 890, wins: 445, winrate: 50.0 },
    achievements: ['Машинное обучение'],
    isAI: true,
    joinDate: '2024-01-01',
  },
  8: {
    id: 8,
    name: 'Neural_1',
    avatar: '1',
    color: 'bg-fuchsia-500',
    bio: 'AI-агент v1.9.9 | Обучение: 2M партий',
    stats: { games: 420, wins: 198, winrate: 47.1 },
    achievements: [],
    isAI: true,
    joinDate: '2024-01-01',
  },
}

const mockGameState = {
  currentScreen: 'welcome',
  roomId: 'TM-2847',
  isHost: true,
  phase: 'day',
  players: [
    { id: 1, name: 'Alexey', avatar: 'A', isAlive: true, isAI: false, profile: playerProfiles[1] },
    { id: 2, name: 'Maria', avatar: 'M', isAlive: true, isAI: false, profile: playerProfiles[2] },
    { id: 3, name: 'Dmitry', avatar: 'D', isAlive: true, isAI: false, profile: playerProfiles[3] },
    { id: 4, name: 'Elena', avatar: 'E', isAlive: true, isAI: false, profile: playerProfiles[4] },
    { id: 5, name: 'Sergey', avatar: 'S', isAlive: false, isAI: false, profile: playerProfiles[5] },
    { id: 6, name: 'Neural_7', avatar: '7', isAlive: true, isAI: true, profile: playerProfiles[6] },
    { id: 7, name: 'Neural_3', avatar: '3', isAlive: true, isAI: true, profile: playerProfiles[7] },
    { id: 8, name: 'Neural_1', avatar: '1', isAlive: true, isAI: true, profile: playerProfiles[8] },
  ],
  messages: [
    { id: 1, player: 'Alexey', text: 'Добрый день, игроки. Начнём с обсуждения кандидатов.', isAI: false },
    { id: 2, player: 'Neural_7', text: 'Предлагаю исключить игрока с подозрительной активностью в чате.', isAI: true },
    { id: 3, player: 'Maria', text: 'Согласна с Alexey. Нужно голосовать.', isAI: false },
  ],
  neuralMemory: [
    { day: 1, summary: 'Выбыл: Sergey. Голоса: Elena(3), Dmitry(2), Sergey(2)' },
    { day: 2, summary: 'Подозрительная активность от Neural_7 в ночной фазе.' },
  ],
  onlineRooms: [
    { id: 'TM-1203', players: 3, maxPlayers: 10 },
    { id: 'TM-2847', players: 5, maxPlayers: 10 },
    { id: 'TM-9912', players: 8, maxPlayers: 10 },
  ],
}

function ThemeToggle({ theme, setTheme }) {
  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className={`p-3 rounded-full transition-all hover:scale-[1.02] active:scale-95 ${
        theme === 'dark' 
          ? 'bg-slate-800 text-amber-400 hover:bg-slate-700' 
          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
      }`}
    >
      {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
    </button>
  )
}

function ProfileModal({ player, theme, onClose }) {
  const p = playerProfiles[player.id]
  if (!p) return null

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div 
        className={`w-full max-w-md rounded-[32px] overflow-hidden ${theme === 'dark' ? 'bg-slate-800' : 'bg-white'}`}
        onClick={e => e.stopPropagation()}
      >
        <div className={`h-32 ${p.color} relative`}>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full bg-black/20 text-white hover:bg-black/30 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 pb-6 -mt-12">
          <div className={`w-24 h-24 rounded-full ${p.color} flex items-center justify-center text-3xl font-bold text-white border-4 ${theme === 'dark' ? 'border-slate-800' : 'border-white'}`}>
            {p.avatar}
          </div>

          <div className="mt-4">
            <div className="flex items-center gap-2">
              <h2 className={`text-2xl font-semibold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>
                {p.name}
              </h2>
              {p.isAI && (
                <span className="px-2 py-1 bg-indigo-600 text-white text-xs rounded-full">AI</span>
              )}
            </div>
            <p className={`mt-1 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
              {p.bio}
            </p>
          </div>

          <div className={`mt-6 grid grid-cols-3 gap-4 p-4 rounded-[24px] ${theme === 'dark' ? 'bg-slate-700/50' : 'bg-slate-50'}`}>
            <div className="text-center">
              <div className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>
                {p.stats.games}
              </div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
                Игр
              </div>
            </div>
            <div className="text-center">
              <div className={`text-2xl font-bold ${theme === 'dark' ? 'text-white' : 'text-slate-900'}`}>
                {p.stats.wins}
              </div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
                Побед
              </div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-emerald-500">
                {p.stats.winrate}%
              </div>
              <div className={`text-xs ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
                Winrate
              </div>
            </div>
          </div>

          {p.achievements.length > 0 && (
            <div className="mt-6">
              <h3 className={`text-sm font-medium mb-3 ${theme === 'dark' ? 'text-slate-400' : 'text-slate-500'}`}>
                Достижения
              </h3>
              <div className="flex flex-wrap gap-2">
                {p.achievements.map((ach, i) => (
                  <span
                    key={i}
                    className={`px-3 py-1 rounded-full text-sm ${
                      theme === 'dark' ? 'bg-indigo-900/50 text-indigo-300' : 'bg-indigo-100 text-indigo-700'
                    }`}
                  >
                    {ach}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className={`mt-6 flex items-center gap-2 text-sm ${theme === 'dark' ? 'text-slate-500' : 'text-slate-400'}`}>
            <Clock className="w-4 h-4" />
            <span>Присоединился {p.joinDate}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function WelcomeScreen({ gameState, setGameState, theme, setTheme }) {
  const [joinId, setJoinId] = useState('')
  const [hoveredRoom, setHoveredRoom] = useState(null)

  const bg = theme === 'dark' ? 'bg-slate-900' : 'bg-slate-50'
  const cardBg = theme === 'dark' ? 'bg-slate-800' : 'bg-white'
  const border = theme === 'dark' ? 'border-slate-700' : 'border-slate-200'
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = theme === 'dark' ? 'text-slate-400' : 'text-slate-500'

  return (
    <div className={`min-h-screen ${bg} flex flex-col items-center justify-center p-8`}>
      <div className="absolute top-6 right-6">
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>

      <div className="max-w-2xl w-full space-y-12">
        <div className="text-center space-y-4">
          <h1 className={`text-6xl font-light tracking-tighter ${textPrimary}`}>
            Turing Mafia
          </h1>
          <p className={`${textSecondary} text-lg`}>Играй с AI-агентами нового поколения</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => setGameState({ ...gameState, currentScreen: 'lobby' })}
            className="bg-indigo-600 text-white p-6 rounded-[32px] hover:scale-[1.02] active:scale-95 transition-all duration-200 flex flex-col items-center gap-3 shadow-lg shadow-indigo-600/20"
          >
            <Plus className="w-8 h-8" />
            <span className="text-lg font-medium">Создать комнату</span>
          </button>

          <div className={`${cardBg} p-6 rounded-[32px] border ${border} hover:scale-[1.02] active:scale-95 transition-all duration-200 flex flex-col gap-4`}>
            <div className="flex items-center gap-3">
              <Users className={`w-6 h-6 ${textSecondary}`} />
              <span className={`text-lg font-medium ${textPrimary}`}>Присоединиться</span>
            </div>
            <input
              type="text"
              placeholder="Введите ID комнаты"
              value={joinId}
              onChange={(e) => setJoinId(e.target.value)}
              className={`w-full px-4 py-3 ${theme === 'dark' ? 'bg-slate-700 text-white placeholder-slate-400' : 'bg-slate-50 text-slate-900 placeholder-slate-400'} rounded-full outline-none focus:ring-2 focus:ring-indigo-600`}
            />
            <button
              onClick={() => joinId && setGameState({ ...gameState, currentScreen: 'lobby' })}
              className={`w-full py-3 ${theme === 'dark' ? 'bg-slate-700 text-slate-200 hover:bg-slate-600' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'} rounded-full transition-colors font-medium`}
            >
              Войти
            </button>
          </div>
        </div>

        <div className="space-y-4">
          <h2 className={`text-xl font-medium ${textPrimary}`}>Online</h2>
          <div className="flex gap-4 overflow-x-auto pb-2">
            {mockGameState.onlineRooms.map((room) => (
              <div
                key={room.id}
                onMouseEnter={() => setHoveredRoom(room.id)}
                onMouseLeave={() => setHoveredRoom(null)}
                className={`${cardBg} p-4 rounded-[32px] border ${border} min-w-[200px] hover:scale-[1.02] active:scale-95 transition-all duration-200 cursor-pointer relative`}
              >
                <div className={`font-medium ${textPrimary}`}>{room.id}</div>
                <div className={`text-sm ${textSecondary}`}>{room.players}/{room.maxPlayers} игроков</div>
                {hoveredRoom === room.id && (
                  <button
                    onClick={() => setGameState({ ...gameState, currentScreen: 'lobby' })}
                    className="absolute inset-0 bg-indigo-600 text-white rounded-[32px] flex items-center justify-center font-medium"
                  >
                    Вход
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function LobbyScreen({ gameState, setGameState, theme, setTheme }) {
  const [selectedPlayer, setSelectedPlayer] = useState(null)

  const bg = theme === 'dark' ? 'bg-slate-900' : 'bg-slate-50'
  const cardBg = theme === 'dark' ? 'bg-slate-800' : 'bg-white'
  const border = theme === 'dark' ? 'border-slate-700' : 'border-slate-200'
  const textPrimary = theme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = theme === 'dark' ? 'text-slate-400' : 'text-slate-500'

  return (
    <div className={`min-h-screen ${bg} p-8`}>
      <div className="absolute top-6 right-6 flex items-center gap-4">
        <ThemeToggle theme={theme} setTheme={setTheme} />
      </div>

      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-light tracking-tighter ${textPrimary}`}>Комната {gameState.roomId}</h1>
            <p className={textSecondary}>Ожидание игроков...</p>
          </div>
          <button
            onClick={() => setGameState({ ...gameState, currentScreen: 'welcome' })}
            className={`px-6 py-3 ${cardBg} rounded-full border ${border} ${textPrimary} hover:scale-[1.02] active:scale-95 transition-all`}
          >
            Назад
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4">
          {gameState.players.map((player) => (
            <button
              key={player.id}
              onClick={() => setSelectedPlayer(player)}
              className={`${cardBg} p-6 rounded-[32px] border ${border} hover:scale-[1.02] active:scale-95 transition-all flex flex-col items-center gap-3`}
            >
              <div className={`w-16 h-16 rounded-full ${playerProfiles[player.id]?.color || 'bg-slate-500'} flex items-center justify-center text-2xl font-medium text-white`}>
                {player.avatar}
              </div>
              <div className={`font-medium text-center ${textPrimary}`}>{player.name}</div>
              {player.isAI && (
                <div className="flex items-center gap-1 text-indigo-600 text-xs">
                  <Bot className="w-3 h-3" />
                  <span>AI</span>
                </div>
              )}
              <div className={`flex items-center gap-1 ${textSecondary} text-xs`}>
                <User className="w-3 h-3" />
                <span>Профиль</span>
                <ChevronRight className="w-3 h-3" />
              </div>
            </button>
          ))}
        </div>

        <div className={`bg-amber-50 dark:bg-amber-900/30 p-4 rounded-[32px] border border-amber-200 dark:border-amber-700`}>
          <div className="flex items-center gap-3 text-amber-800 dark:text-amber-300">
            <Bot className="w-5 h-5" />
            <span className="font-medium">5 мест зарезервировано под AI-агентов</span>
          </div>
        </div>

        {gameState.isHost && (
          <div className="flex justify-center">
            <button
              onClick={() => setGameState({ ...gameState, currentScreen: 'game' })}
              className="fixed bottom-8 right-8 bg-indigo-600 text-white p-6 rounded-full shadow-lg shadow-indigo-600/30 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-3"
            >
              <Play className="w-6 h-6" />
              <span className="font-medium">Начать игру</span>
            </button>
          </div>
        )}
      </div>

      {selectedPlayer && (
        <ProfileModal player={selectedPlayer} theme={theme} onClose={() => setSelectedPlayer(null)} />
      )}
    </div>
  )
}

function GameScreen({ gameState, setGameState, theme, setTheme }) {
  const [newMessage, setNewMessage] = useState('')
  const [selectedPlayer, setSelectedPlayer] = useState(null)
  const isNight = gameState.phase === 'night'

  const handleSendMessage = () => {
    if (newMessage.trim()) {
      const message = {
        id: gameState.messages.length + 1,
        player: 'Alexey',
        text: newMessage,
        isAI: false,
      }
      setGameState({
        ...gameState,
        messages: [...gameState.messages, message],
      })
      setNewMessage('')
    }
  }

  const togglePhase = () => {
    setGameState({
      ...gameState,
      phase: gameState.phase === 'day' ? 'night' : 'day',
    })
  }

  const currentTheme = isNight ? 'dark' : theme

  const bg = currentTheme === 'dark' ? 'bg-slate-900' : 'bg-slate-50'
  const headerBg = currentTheme === 'dark' ? 'bg-slate-800' : 'bg-white'
  const cardBg = currentTheme === 'dark' ? 'bg-slate-800' : 'bg-white'
  const border = currentTheme === 'dark' ? 'border-slate-700' : 'border-slate-200'
  const textPrimary = currentTheme === 'dark' ? 'text-white' : 'text-slate-900'
  const textSecondary = currentTheme === 'dark' ? 'text-slate-400' : 'text-slate-500'
  const inputBg = currentTheme === 'dark' ? 'bg-slate-700' : 'bg-slate-50'

  return (
    <div className={`min-h-screen ${bg} transition-colors duration-1000`}>
      <div className={`${headerBg} px-6 py-4 flex items-center justify-between border-b ${border}`}>
        <div className="flex items-center gap-4">
          <h1 className={`text-xl font-light tracking-tight ${textPrimary}`}>
            Turing Mafia
          </h1>
          <span className={`text-sm ${textSecondary}`}>
            {gameState.roomId}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle theme={theme} setTheme={setTheme} />
          <button
            onClick={togglePhase}
            className={`flex items-center gap-3 px-6 py-3 rounded-full ${isNight ? 'bg-slate-700 text-amber-400' : 'bg-indigo-600 text-white'} hover:scale-[1.02] active:scale-95 transition-all`}
          >
            {isNight ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            <span className="font-medium">{isNight ? 'Ночь' : 'День'}</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-5 h-[calc(100vh-73px)]">
        <div className="p-4 space-y-3 overflow-y-auto">
          <h2 className={`text-sm font-medium mb-4 ${textSecondary}`}>
            Игроки ({gameState.players.filter(p => p.isAlive).length}/{gameState.players.length})
          </h2>
          {gameState.players.map((player) => (
            <button
              key={player.id}
              onClick={() => setSelectedPlayer(player)}
              className={`w-full p-4 rounded-[28px] ${player.isAlive ? cardBg : (currentTheme === 'dark' ? 'bg-slate-800/50' : 'bg-slate-100')} ${player.isAI ? 'border border-indigo-500/30' : ''} ${border} flex items-center gap-3 hover:scale-[1.01] active:scale-[0.99] transition-all`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium ${playerProfiles[player.id]?.color || 'bg-slate-500'} ${
                player.isAlive ? 'text-white' : 'text-slate-400'
              }`}>
                {player.avatar}
              </div>
              <div className="flex-1 text-left">
                <div className={`font-medium ${textPrimary} ${!player.isAlive && 'line-through opacity-50'}`}>
                  {player.name}
                </div>
                {player.isAI && (
                  <div className="flex items-center gap-1">
                    <Bot className="w-3 h-3 text-indigo-400" />
                    <span className="text-xs text-indigo-400">AI</span>
                  </div>
                )}
                {!player.isAlive && (
                  <div className="flex items-center gap-1">
                    <Skull className="w-3 h-3 text-slate-400" />
                    <span className="text-xs text-slate-400">Мёртв</span>
                  </div>
                )}
              </div>
            </button>
          ))}
        </div>

        <div className={`col-span-2 p-4 flex flex-col ${currentTheme === 'dark' ? 'bg-slate-800/50' : 'bg-white'} border-x ${border}`}>
          <h2 className={`text-sm font-medium mb-4 ${textSecondary}`}>
            Чат
          </h2>
          <div className="flex-1 overflow-y-auto space-y-8 pb-4">
            {gameState.messages.map((message) => (
              <div key={message.id} className="space-y-1">
                <div className={`font-semibold flex items-center gap-2 ${textPrimary}`}>
                  {message.player}
                  {message.isAI && <Bot className="w-4 h-4 text-indigo-400" />}
                </div>
                <p className={textSecondary}>{message.text}</p>
              </div>
            ))}
          </div>
          <div className={`mt-4 flex items-center gap-2 ${inputBg} p-2 rounded-full`}>
            <button className={`p-3 rounded-full ${currentTheme === 'dark' ? 'hover:bg-slate-600' : 'hover:bg-slate-200'} transition-colors`}>
              <Mic className={`w-5 h-5 ${textSecondary}`} />
            </button>
            <input
              type="text"
              value={newMessage}
              onChange={(e) => setNewMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Введите сообщение..."
              className={`flex-1 bg-transparent outline-none ${textPrimary} placeholder-slate-400`}
            />
            <button
              onClick={handleSendMessage}
              className="p-3 bg-indigo-600 text-white rounded-full hover:bg-indigo-700 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="col-span-2 p-4">
          <h2 className={`text-sm font-medium mb-4 ${textSecondary}`}>
            Neural Memory
          </h2>
          <div className="space-y-4">
            {gameState.neuralMemory.map((item, index) => (
              <div
                key={index}
                className={`p-4 rounded-[32px] ${cardBg} border ${border}`}
              >
                <div className={`text-xs font-medium mb-2 ${isNight ? 'text-indigo-400' : 'text-indigo-600'}`}>
                  День {item.day}
                </div>
                <p className={`text-sm ${textSecondary}`}>
                  {item.summary}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-8">
            <h3 className={`text-sm font-medium mb-4 ${textSecondary}`}>
              Голосование
            </h3>
            <div className="space-y-2">
              {gameState.players.filter(p => p.isAlive).map((player) => (
                <button
                  key={player.id}
                  className={`w-full p-4 rounded-[28px] ${cardBg} hover:${currentTheme === 'dark' ? 'bg-slate-700' : 'bg-slate-50'} border ${border} flex items-center justify-between transition-all hover:scale-[1.01] active:scale-[0.99]`}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full ${playerProfiles[player.id]?.color || 'bg-slate-500'} flex items-center justify-center text-sm font-medium text-white`}>
                      {player.avatar}
                    </div>
                    <span className={`font-medium ${textPrimary}`}>
                      {player.name}
                    </span>
                  </div>
                  <span className={`text-sm ${textSecondary}`}>
                    0 голосов
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {selectedPlayer && (
        <ProfileModal player={selectedPlayer} theme={theme} onClose={() => setSelectedPlayer(null)} />
      )}
    </div>
  )
}

export default function App() {
  const [gameState, setGameState] = useState(mockGameState)
  const [theme, setTheme] = useState('light')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return (
    <div className="font-sans antialiased">
      {gameState.currentScreen === 'welcome' && (
        <WelcomeScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} />
      )}
      {gameState.currentScreen === 'lobby' && (
        <LobbyScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} />
      )}
      {gameState.currentScreen === 'game' && (
        <GameScreen gameState={gameState} setGameState={setGameState} theme={theme} setTheme={setTheme} />
      )}
    </div>
  )
}
