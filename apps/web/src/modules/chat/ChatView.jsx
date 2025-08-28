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

  function buildPrintableHTML(title, msgs){
    const esc = (s) => (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    const items = (Array.isArray(msgs)?msgs:[]).map(m => {
      const content = esc(m?.content || m?.assistant || '')
      const date = m?.created_at ? new Date(m.created_at).toLocaleString() : ''
      const role = esc(m?.role || (m?.assistant ? 'assistant':'user'))
      return `<div class="msg"><div class="meta"><span class="role">${role}</span> <span class="date">${date}</span></div><div class="content">${content.replace(/\n/g,'<br/>')}</div></div>`
    }).join('')
    return `<!doctype html><html><head><meta charset="utf-8"><title>${esc(title||'Conversation')}</title>
    <style>body{font-family:Arial,Helvetica,sans-serif;color:#0f172a;padding:24px}h1{margin:0 0 16px;font-size:18px}.msg{border:1px solid #e2e8f0;border-radius:8px;padding:12px;margin:10px 0}.meta{font-size:12px;color:#475569;margin-bottom:6px}.role{font-weight:600;margin-right:8px}.content{white-space:pre-wrap}</style>
    </head><body><h1>${esc(title||'Conversation')}</h1>${items}</body></html>`
  }

  async function copyLastAssistant(){
    const text = lastAssistant || ''
    if (!text) return
    await navigator.clipboard?.writeText(text)
    alert('Réponse copiée')
  }

  async function copyWholeConversation(){
    const arr = Array.isArray(messages)?messages:[]
    const text = arr.map(m => {
      const d = m?.created_at ? new Date(m.created_at).toLocaleString() : ''
      return `[${d}] ${m?.role || (m?.assistant?'assistant':'user')}:\n${m?.content || m?.assistant || ''}`
    }).join('\n\n')
    await navigator.clipboard?.writeText(text)
    alert('Conversation copiée')
  }

  return (
    <section className="flex-1 flex flex-col relative">
      <div className="border-b bg-white dark:bg-slate-900 dark:border-slate-700 p-3 flex items-center justify-between">
        <h2 className="font-semibold text-slate-900 dark:text-slate-100">{conversation?.title || 'Nouvelle conversation'}</h2>
        {conversation?.id && (
          <div className="flex items-center gap-2">
            <button
              className="px-2.5 py-1.5 text-xs rounded border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
              onClick={copyLastAssistant}
            >Copier la réponse</button>
            <button
              className="px-2.5 py-1.5 text-xs rounded border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
              onClick={copyWholeConversation}
            >Copier la conversation</button>
            <button
              className="px-2.5 py-1.5 text-xs rounded border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
              onClick={async ()=>{
                try {
                  const blob = await api.exportConversation(conversation.id, 'pdf')
                  const url = URL.createObjectURL(blob)
                  const a = document.createElement('a')
                  a.href = url
                  a.download = `conversation_${conversation.id}.pdf`
                  a.click()
                  URL.revokeObjectURL(url)
                } catch (e) {
                  // Fallback: ouvrir une page imprimable, l'utilisateur peut enregistrer en PDF
                  const html = buildPrintableHTML(conversation?.title, messages)
                  const w = window.open('', '_blank')
                  if (w) {
                    w.document.open()
                    w.document.write(html)
                    w.document.close()
                    w.focus()
                    setTimeout(()=>{ try { w.print() } catch(e){} }, 300)
                  } else {
                    alert("Impossible d'ouvrir la fenêtre d'impression. Veuillez autoriser les popups.")
                  }
                }
              }}
            >PDF</button>
            <button
              className="px-2.5 py-1.5 text-xs rounded border border-slate-300 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
              onClick={async ()=>{
                const blob = await api.exportConversation(conversation.id, 'docx')
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `conversation_${conversation.id}.docx`
                a.click()
                URL.revokeObjectURL(url)
              }}
            >Word</button>
            <button
              className="px-2.5 py-1.5 text-xs rounded border border-slate-300 bg-white hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
              onClick={async ()=>{
                const blob = await api.exportConversation(conversation.id, 'xlsx')
                const url = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = url
                a.download = `conversation_${conversation.id}.xlsx`
                a.click()
                URL.revokeObjectURL(url)
              }}
            >Excel</button>
          </div>
        )}
      </div>
      {isLoading ? <div className="p-4 text-slate-500">Chargement…</div> : (
        <>
          <MessageList messages={messages || []} />
          {sendMutation.isPending && (
            <div className="px-4 pb-2 text-sm text-slate-700 dark:text-slate-200">
              <span className="opacity-70">Assistant est en train d'écrire…</span>
              <div className="mt-2 p-3 bg-white border border-slate-200 rounded text-slate-900 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100">{typing}</div>
            </div>
          )}
        </>
      )}
      {!!(conversation?.id && lastAssistant) && (
        <div className="fixed right-4 bottom-20 md:bottom-24 z-30">
          <button
            aria-label="Copier la dernière réponse"
            className="px-3 py-2 text-xs rounded shadow-lg border border-slate-300 bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
            onClick={copyLastAssistant}
          >
            Copier la dernière réponse
          </button>
        </div>
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
