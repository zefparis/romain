import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'

export default function CrisesView(){
  const [filters, setFilters] = useState({ country: '', q: '' })
  const [page, setPage] = useState({ limit: 50, offset: 0 })
  const { data, isLoading, isError } = useQuery({
    queryKey: ['humdata','crises', filters, page],
    queryFn: () => api.humdata.crises({
      source: 'reliefweb',
      limit: page.limit,
      offset: page.offset,
      country: filters.country || undefined,
      q: filters.q || undefined,
    })
  })
  const list = data || []

  if (isLoading) return <div className="p-4 text-slate-700 dark:text-slate-200">Chargement…</div>
  if (isError) return <div className="p-4 text-red-600">Erreur de chargement</div>

  return (
    <div className="flex-1 overflow-auto p-4 bg-slate-50 dark:bg-slate-900">
      <h2 className="text-lg font-semibold mb-3 text-slate-900 dark:text-slate-100">Crises (ReliefWeb)</h2>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="block text-xs text-slate-600 dark:text-slate-400">Pays</label>
          <input value={filters.country}
                 onChange={(e)=>setFilters(f=>({...f, country: e.target.value}))}
                 className="border rounded px-2 py-1 bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100 dark:border-slate-600" placeholder="Somalia" />
        </div>
        <div>
          <label className="block text-xs text-slate-600 dark:text-slate-400">Texte</label>
          <input value={filters.q}
                 onChange={(e)=>setFilters(f=>({...f, q: e.target.value}))}
                 className="border rounded px-2 py-1 bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100 dark:border-slate-600" placeholder="mots-clés" />
        </div>
        <div>
          <label className="block text-xs text-slate-600 dark:text-slate-400">Page size</label>
          <select
            value={page.limit}
            onChange={(e)=>setPage(p=>({ ...p, offset: 0, limit: parseInt(e.target.value) }))}
            className="border rounded px-2 py-1 bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100 dark:border-slate-600"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
        <div className="md:ml-auto flex gap-2 w-full md:w-auto">
          <button
            onClick={()=>setPage(p=>({ ...p, offset: Math.max(0, p.offset - p.limit) }))}
            disabled={page.offset === 0 || isLoading}
            className={`px-3 py-1 rounded border bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700 ${page.offset===0||isLoading?'opacity-50':''}`}
          >Précédent</button>
          <button
            onClick={()=>setPage(p=>({ ...p, offset: p.offset + p.limit }))}
            disabled={isLoading || (list.length < page.limit)}
            className={`px-3 py-1 rounded border bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700 ${isLoading||list.length<page.limit?'opacity-50':''}`}
          >Suivant</button>
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-sm text-slate-600 dark:text-slate-400">
        <div className="min-w-[200px]">
          Affichage {list.length ? (page.offset + 1) : 0}
          –{page.offset + list.length}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs">Aller à la page</label>
          <input
            type="number"
            min={1}
            value={Math.floor(page.offset / page.limit) + 1}
            onChange={(e)=>{
              const n = Math.max(1, parseInt(e.target.value) || 1)
              setPage(p=>({ ...p, offset: (n - 1) * p.limit }))
            }}
            className="w-20 border rounded px-2 py-1 bg-white text-slate-900 dark:bg-slate-900 dark:text-slate-100 dark:border-slate-600"
          />
          <button
            onClick={()=>{ setFilters({ country: '', q: '' }); setPage(p=>({ ...p, offset: 0 })) }}
            className="px-3 py-1 rounded border bg-white text-slate-900 hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:text-slate-100 dark:border-slate-600 dark:hover:bg-slate-700"
          >Reset filtres</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {list.map(item => (
          <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="block p-3 rounded border bg-white hover:shadow focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:bg-slate-800 dark:border-slate-700">
            <div className="font-medium text-slate-900 dark:text-slate-100">{item.title}</div>
            <div className="text-sm text-slate-600 dark:text-slate-400">{item.country || 'Monde'}</div>
            {item.published_at && (
              <div className="text-xs text-slate-500 dark:text-slate-400">{new Date(item.published_at).toLocaleString()}</div>
            )}
          </a>
        ))}
      </div>
    </div>
  )
}
