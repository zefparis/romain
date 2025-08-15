import React from 'react'

export default function MessageList({ messages }){
  return (
    <div className="flex-1 overflow-auto space-y-3 p-4">
      {messages?.map((m,i)=>{
        const isUser = m.role === 'user'
        return (
          <div key={i} className={`max-w-3xl ${isUser ? 'ml-auto' : ''}`}>
            <div className={`px-3 py-2 rounded-lg shadow-sm ${isUser ? 'bg-black text-white' : 'bg-white border'}`}>
              <div className="whitespace-pre-wrap text-sm">{m.content}</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
