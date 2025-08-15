import React, { useEffect, useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '../lib/queryClient'
import Sidebar from './sidebar/Sidebar'
import ChatView from './chat/ChatView'
import DocumentsView from './documents/DocumentsView'
import CrisesView from './humdata/CrisesView'
import JobsView from './humdata/JobsView'
import FundingView from './humdata/FundingView'
import { api } from '../lib/api'

export default function App(){
  const [current, setCurrent] = useState(null)
  const [tab, setTab] = useState('chat') // 'chat' | 'docs' | 'crises' | 'jobs' | 'funding'
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [theme, setTheme] = useState(()=>{
    try {
      const saved = localStorage.getItem('theme')
      if (saved === 'dark' || saved === 'light') return saved
    } catch (_) {}
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    return prefersDark ? 'dark' : 'light'
  })

  useEffect(()=>{
    const root = document.documentElement
    if (theme === 'dark') root.classList.add('dark'); else root.classList.remove('dark')
    try { localStorage.setItem('theme', theme) } catch (_) {}
  }, [theme])

  // Create a new conversation if none selected on first load
  async function ensureConversation(){
    if (current) return current
    const c = await api.createConversation('Nouvelle conversation')
    setCurrent(c)
    return c
  }

  async function onNewConversation(){
    const c = await api.createConversation('Nouvelle conversation')
    setCurrent(c)
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-900 dark:text-slate-100 flex flex-col md:flex-row safe-area-px">
        {/* Sidebar: hidden on mobile unless toggled */}
        <div className={`md:block ${sidebarOpen ? 'block' : 'hidden'} md:static fixed inset-0 z-40 md:z-auto`}>
          <div className={`absolute inset-0 bg-black/40 md:hidden ${sidebarOpen ? 'block' : 'hidden'}`} onClick={()=>setSidebarOpen(false)} />
          <div className="relative md:relative md:translate-x-0 w-72 max-w-[80vw] h-screen md:h-screen bg-white dark:bg-slate-800 shadow md:shadow-none">
            <Sidebar currentId={current?.id} onSelect={(c)=>{ setCurrent(c); setSidebarOpen(false) }} onNew={async ()=>{ await onNewConversation(); setSidebarOpen(false) }} />
          </div>
        </div>
        <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-0">
          <header className="p-2 md:p-4 border-b bg-white dark:bg-slate-900 dark:border-slate-700 flex items-center justify-between gap-2 sticky top-0 z-30">
            <div className="flex items-center gap-2">
              <button className="md:hidden inline-flex items-center justify-center w-10 h-10 rounded border tap-transparent touch-manipulation" onClick={()=>setSidebarOpen(s=>!s)} aria-label="Ouvrir le menu">
                <span className="i--menu">≡</span>
              </button>
              <h1 className="text-base md:text-xl font-bold truncate">Assistant Romain</h1>
            </div>
            <nav className="hidden md:flex flex-wrap gap-2 justify-end items-center">
              <button
                onClick={()=>setTab('chat')}
                className={`px-3 py-2 rounded tap-transparent touch-manipulation text-sm md:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
                  ${tab==='chat'
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600'}`}
              >Chat</button>
              <button
                onClick={()=>setTab('docs')}
                className={`px-3 py-2 rounded tap-transparent touch-manipulation text-sm md:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
                  ${tab==='docs'
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600'}`}
              >Documents</button>
              <button
                onClick={()=>setTab('crises')}
                className={`px-3 py-2 rounded tap-transparent touch-manipulation text-sm md:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
                  ${tab==='crises'
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600'}`}
              >Crises</button>
              <button
                onClick={()=>setTab('jobs')}
                className={`px-3 py-2 rounded tap-transparent touch-manipulation text-sm md:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
                  ${tab==='jobs'
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600'}`}
              >Emplois</button>
              <button
                onClick={()=>setTab('funding')}
                className={`px-3 py-2 rounded tap-transparent touch-manipulation text-sm md:text-base focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500
                  ${tab==='funding'
                    ? 'bg-blue-600 text-white dark:bg-blue-500'
                    : 'bg-slate-200 text-slate-900 hover:bg-slate-300 dark:bg-slate-700 dark:text-slate-100 dark:hover:bg-slate-600'}`}
              >Financements</button>
              <button onClick={()=>setTheme(t=>t==='dark'?'light':'dark')} className="ml-2 px-3 py-2 rounded border text-sm md:text-base bg-white dark:bg-slate-800 dark:border-slate-700" aria-label="Basculer le thème">
                {theme==='dark' ? '☀️ Clair' : '🌙 Sombre'}
              </button>
            </nav>
          </header>
          <main className="flex-1 flex min-w-0">
            {tab==='chat' ? (
              current ? (
                <ChatView conversation={current} />
              ) : (
                <div className="p-6 text-slate-600 dark:text-slate-300">
                  <button onClick={ensureConversation} className="px-4 py-2 rounded bg-black text-white dark:bg-slate-100 dark:text-slate-900">Nouvelle conversation</button>
                </div>
              )
            ) : tab==='docs' ? (
              <DocumentsView />
            ) : tab==='crises' ? (
              <CrisesView />
            ) : tab==='jobs' ? (
              <JobsView />
            ) : (
              <FundingView />
            )}
          </main>

          {/* Bottom Tab Bar (mobile only) */}
          <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/70 dark:bg-slate-900/90 dark:border-slate-700">
            <ul className="grid grid-cols-5">
              <li>
                <button onClick={()=>setTab('chat')} className={`w-full py-2 text-xs leading-tight flex flex-col items-center justify-center ${tab==='chat' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}`}>Chat</button>
              </li>
              <li>
                <button onClick={()=>setTab('docs')} className={`w-full py-2 text-xs leading-tight flex flex-col items-center justify-center ${tab==='docs' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}`}>Docs</button>
              </li>
              <li>
                <button onClick={()=>setTab('crises')} className={`w-full py-2 text-xs leading-tight flex flex-col items-center justify-center ${tab==='crises' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}`}>Crises</button>
              </li>
              <li>
                <button onClick={()=>setTab('jobs')} className={`w-full py-2 text-xs leading-tight flex flex-col items-center justify-center ${tab==='jobs' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}`}>Emplois</button>
              </li>
              <li>
                <button onClick={()=>setTab('funding')} className={`w-full py-2 text-xs leading-tight flex flex-col items-center justify-center ${tab==='funding' ? 'text-blue-600 dark:text-blue-400' : 'text-slate-700 dark:text-slate-200'}`}>Funds</button>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </QueryClientProvider>
  )
}

