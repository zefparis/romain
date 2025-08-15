import React, { useState } from 'react'
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export default function App(){
  const [q,setQ]=useState('Bonjour, prépare un plan de rapport.')
  const [a,setA]=useState('')
  const [loading,setLoading]=useState(false)
  async function send(){
    setLoading(true)
    const r=await fetch(`${API}/chat/complete`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:q})})
    const j=await r.json(); setA(j.reply); setLoading(false)
  }
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="max-w-5xl mx-auto p-6">
        <h1 className="text-2xl font-bold">Assistant Romain</h1>
        <div className="mt-4 grid gap-3">
          <textarea className="w-full p-3 border rounded-lg" rows={5} value={q} onChange={e=>setQ(e.target.value)} />
          <button onClick={send} disabled={loading} className="px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50">{loading?'…':'Envoyer'}</button>
          <pre className="p-3 bg-white border rounded-lg whitespace-pre-wrap">{a}</pre>
        </div>
      </div>
    </div>
  )
}
