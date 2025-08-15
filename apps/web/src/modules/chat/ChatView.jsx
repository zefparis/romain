import React, { useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../../lib/api'
import MessageList from './MessageList'
import ChatInput from './ChatInput'

export default function ChatView({ conversation, onFirstResponse }){
  const qc = useQueryClient()
  const { data: messages, isLoading } = useQuery({
    queryKey: ['messages', conversation?.id],
    queryFn: () => api.getMessages(conversation.id),
    enabled: !!conversation?.id,
  })

  const [typing, setTyping] = useState('')
  const sendMutation = useMutation({
    mutationFn: async (text) => {
      setTyping('')
      await api.streamComplete({
        message: text,
        onToken: (t) => setTyping((prev) => prev + t)
      })
      // À la fin du stream, on envoie réellement le message pour persister dans la conversation
      return api.sendMessage({ conversation_id: conversation.id, message: text })
    },
    onSuccess: () => {
      setTyping('')
      qc.invalidateQueries({ queryKey: ['messages', conversation.id] })
    },
    onError: () => setTyping('')
  })

  const lastAssistant = useMemo(() => {
    if (!messages || !Array.isArray(messages)) return ''
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i]
      if (m?.role === 'assistant' && typeof m?.content === 'string') return m.content
      if (m?.assistant) return m.assistant
    }
    return ''
  }, [messages])

  return (
    <section className="flex-1 flex flex-col">
      <div className="border-b bg-white p-3">
        <h2 className="font-semibold">{conversation?.title || 'Nouvelle conversation'}</h2>
      </div>
      {isLoading ? <div className="p-4 text-slate-500">Chargement…</div> : (
        <>
          <MessageList messages={messages || []} />
          {sendMutation.isPending && (
            <div className="px-4 pb-2 text-slate-700 text-sm">
              <span className="opacity-60">Assistant est en train d'écrire…</span>
              <div className="mt-2 p-3 bg-white border rounded">{typing}</div>
            </div>
          )}
        </>
      )}
      <ChatInput
        disabled={sendMutation.isPending || !conversation}
        onSend={(t)=>sendMutation.mutate(t)}
        typing={typing}
        lastAssistant={lastAssistant}
      />
    </section>
  )
}
