import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'

export default function JobsView(){
  const [filters, setFilters] = useState({ org: '', country: '', q: '' })
  const [page, setPage] = useState({ limit: 50, offset: 0 })
  const { data, isLoading, isError } = useQuery({
    queryKey: ['humdata','jobs', filters, page],
    queryFn: () => api.humdata.jobs({
      source: 'reliefweb',
      limit: page.limit,
      offset: page.offset,
      q: filters.q || undefined,
      org: filters.org || undefined,
      country: filters.country || undefined,
    })
  })
  const list = data || []

  if (isLoading) return <div className="p-4">Chargement…</div>
  if (isError) return <div className="p-4 text-red-600">Erreur de chargement</div>

  return (
    <div className="flex-1 overflow-auto p-4">
      <h2 className="text-lg font-semibold mb-3">Emplois (ReliefWeb)</h2>
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="block text-xs text-slate-600">Organisation</label>
          <input value={filters.org}
                 onChange={(e)=>setFilters(f=>({...f, org: e.target.value}))}
                 className="border rounded px-2 py-1" placeholder="UNICEF" />
        </div>
        <div>
          <label className="block text-xs text-slate-600">Pays/Lieu</label>
          <input value={filters.country}
                 onChange={(e)=>setFilters(f=>({...f, country: e.target.value}))}
                 className="border rounded px-2 py-1" placeholder="Niger" />
        </div>
        <div>
          <label className="block text-xs text-slate-600">Texte</label>
          <input value={filters.q}
                 onChange={(e)=>setFilters(f=>({...f, q: e.target.value}))}
                 className="border rounded px-2 py-1" placeholder="WASH, MEAL…" />
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-sm text-slate-600">
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
            className="w-20 border rounded px-2 py-1"
          />
          <button
            onClick={()=>{ setFilters({ org: '', country: '', q: '' }); setPage(p=>({ ...p, offset: 0 })) }}
            className="px-3 py-1 rounded border"
          >Reset filtres</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {list.map(item => (
          <a key={item.id} href={item.url} target="_blank" rel="noreferrer" className="block p-3 rounded border bg-white hover:shadow">
            <div className="font-medium">{item.title}</div>
            <div className="text-sm text-slate-600">{item.org || 'Organisation non précisée'} • {item.location || 'Lieu non précisé'}</div>
            <div className="text-xs text-slate-500 flex gap-2">
              {item.published_at && <span>publié {new Date(item.published_at).toLocaleDateString()}</span>}
              {item.deadline && <span>• clôture {new Date(item.deadline).toLocaleDateString()}</span>}
            </div>
          </a>
        ))}
      </div>
      <div className="flex items-center justify-end gap-2 mt-4">
        <div>
          <label className="block text-xs text-slate-600">Page size</label>
          <select
            value={page.limit}
            onChange={(e)=>setPage(p=>({ ...p, offset: 0, limit: parseInt(e.target.value) }))}
            className="border rounded px-2 py-1"
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </div>
        <button
          onClick={()=>setPage(p=>({ ...p, offset: Math.max(0, p.offset - p.limit) }))}
          disabled={page.offset === 0 || isLoading}
          className={`px-3 py-1 rounded border ${page.offset===0||isLoading?'opacity-50':''}`}
        >Précédent</button>
        <button
          onClick={()=>setPage(p=>({ ...p, offset: p.offset + p.limit }))}
          disabled={isLoading || (list.length < page.limit)}
          className={`px-3 py-1 rounded border ${isLoading||list.length<page.limit?'opacity-50':''}`}
        >Suivant</button>
      </div>
    </div>
  )
}
