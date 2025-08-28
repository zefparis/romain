import React from 'react'

export default function MessageList({ messages }){
  return (
    <div className="flex-1 overflow-auto space-y-3 p-4">
      {messages?.map((m,i)=>{
        const isUser = m.role === 'user'
        return (
          <div key={i} className={`group relative max-w-3xl ${isUser ? 'ml-auto' : ''}`}>
            <div className={`px-3 py-2 rounded-lg shadow-sm relative
              ${isUser
                ? 'bg-blue-600 text-white dark:bg-blue-500'
                : 'bg-white border border-slate-200 text-slate-900 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'}
            `}>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>
              {!isUser && (
                <button
                  title="Copier"
                  onClick={async (e)=>{
                    e.stopPropagation()
                    try {
                      await navigator.clipboard?.writeText(m.content || '')
                    } catch {}
                  }}
                  className="hidden group-hover:flex items-center gap-1 absolute -top-2 -right-2 text-[11px] px-2 py-1 rounded bg-slate-800 text-white shadow hover:bg-slate-700"
                >
                  Copier
                </button>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
