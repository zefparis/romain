import React from 'react'

export default function MessageList({ messages }){
  return (
    <div className="flex-1 overflow-auto space-y-3 p-4">
      {messages?.map((m,i)=>{
        const isUser = m.role === 'user'
        return (
          <div key={i} className={`max-w-3xl ${isUser ? 'ml-auto' : ''}`}>
            <div className={`px-3 py-2 rounded-lg shadow-sm
              ${isUser
                ? 'bg-blue-600 text-white dark:bg-blue-500'
                : 'bg-white border border-slate-200 text-slate-900 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100'}
            `}>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{m.content}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
