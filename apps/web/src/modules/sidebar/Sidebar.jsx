import React from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'

export default function Sidebar({ currentId, onSelect, onNew }){
  const qc = useQueryClient()
  const { data, isLoading, isError } = useQuery({ queryKey: ['conversations'], queryFn: api.listConversations })

  return (
    <aside className="w-72 border-r dark:border-slate-700 bg-white dark:bg-slate-800 h-screen p-3 flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h2 className="font-semibold text-slate-900 dark:text-slate-100">Conversations</h2>
        <button
          onClick={async ()=>{ await onNew(); qc.invalidateQueries({queryKey:['conversations']}) }}
          className="text-sm px-2 py-1 rounded bg-black text-white dark:bg-slate-100 dark:text-slate-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >Nouvelle</button>
      </div>
      {isLoading && <div className="text-sm text-slate-500 dark:text-slate-400">Chargement…</div>}
      {isError && <div className="text-sm text-red-600">Erreur de chargement</div>}
      <div className="space-y-1 overflow-auto">
        {data?.map(c => (
          <div key={c.id} className={`group flex items-center gap-2 px-2 py-2 rounded hover:bg-slate-100 dark:hover:bg-slate-700 ${currentId===c.id ? 'bg-slate-200 dark:bg-slate-600' : ''}`}>
            <button
              onClick={()=>onSelect(c)}
              className="flex-1 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            >
              <div className="text-sm font-medium truncate text-slate-900 dark:text-slate-100">{c.title || 'Sans titre'}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">{new Date(c.created_at).toLocaleString()}</div>
            </button>
            <button
              title="Supprimer"
              aria-label="Supprimer la conversation"
              onClick={async (e)=>{
                e.stopPropagation()
                const ok = window.confirm('Supprimer cette conversation ? Cette action est définitive.')
                if (!ok) return
                try {
                  await api.deleteConversation(c.id)
                  if (currentId === c.id) onSelect?.(undefined)
                  qc.invalidateQueries({ queryKey: ['conversations'] })
                } catch (err) {
                  console.error(err)
                  alert('Erreur lors de la suppression')
                }
              }}
              className="shrink-0 inline-flex items-center justify-center w-8 h-8 rounded border text-slate-700 hover:bg-slate-200 dark:text-slate-200 dark:border-slate-600 dark:hover:bg-slate-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
            >
              🗑️
            </button>
          </div>
        ))}
      </div>
    </aside>
  )
}
