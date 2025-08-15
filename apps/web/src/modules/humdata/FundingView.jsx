import React, { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api'

export default function FundingView(){
  const yearNow = new Date().getFullYear()
  const [filters, setFilters] = useState({ year: yearNow, country: '', cluster: '' })
  const [page, setPage] = useState({ limit: 50, offset: 0 })
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['humdata','funding', filters, page],
    queryFn: () => api.humdata.funding({
      year: filters.year || undefined,
      country: filters.country || undefined,
      cluster: filters.cluster || undefined,
      limit: page.limit,
      offset: page.offset,
    })
  })
  const list = data || []
  const pageTotal = useMemo(() => (list||[])
    .reduce((acc, r) => acc + (typeof r.amount === 'number' ? r.amount : (parseFloat(r.amount) || 0)), 0), [list])

  return (
    <div className="flex-1 overflow-auto p-4">
      <div className="flex flex-wrap items-end gap-3 mb-4">
        <div>
          <label className="block text-xs text-slate-600">Année</label>
          <input type="number" value={filters.year}
                 onChange={(e)=>setFilters(f=>({...f, year: parseInt(e.target.value)||''}))}
                 className="border rounded px-2 py-1 w-28" />
        </div>
        <div>
          <label className="block text-xs text-slate-600">Pays</label>
          <input value={filters.country}
                 onChange={(e)=>setFilters(f=>({...f, country: e.target.value}))}
                 className="border rounded px-2 py-1" placeholder="Somalia" />
        </div>
        <div>
          <label className="block text-xs text-slate-600">Cluster</label>
          <input value={filters.cluster}
                 onChange={(e)=>setFilters(f=>({...f, cluster: e.target.value}))}
                 className="border rounded px-2 py-1" placeholder="Health" />
        </div>
        <button onClick={()=>refetch()} className="px-3 py-1 rounded bg-black text-white">Rechercher</button>
        <div className="md:ml-auto flex items-end gap-3 w-full md:w-auto">
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

      {isLoading && <div>Chargement…</div>}
      {isError && <div className="text-red-600">Erreur de chargement</div>}

      <div className="flex flex-wrap items-center justify-between gap-2 mb-2 text-sm text-slate-600">
        <div className="min-w-[220px]">
          Affichage {list.length ? (page.offset + 1) : 0}–{page.offset + list.length}
          {pageTotal ? (
            <span className="ml-3">Total page: {pageTotal.toLocaleString('en-US', { maximumFractionDigits: 0 })} USD</span>
          ) : null}
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
            onClick={()=>{ setFilters({ year: yearNow, country: '', cluster: '' }); setPage(p=>({ ...p, offset: 0 })) }}
            className="px-3 py-1 rounded border"
          >Reset filtres</button>
        </div>
      </div>

      <div className="overflow-auto rounded border bg-white">
        <table className="min-w-[800px] w-full">
          <thead className="bg-slate-100 text-left text-sm">
            <tr>
              <th className="p-2">Donor</th>
              <th className="p-2">Recipient</th>
              <th className="p-2">Pays</th>
              <th className="p-2">Cluster</th>
              <th className="p-2 text-right">Montant (USD)</th>
            </tr>
          </thead>
          <tbody>
            {list.map((r, idx) => (
              <tr key={r.id || idx} className="border-t">
                <td className="p-2">{r.donor || '-'}</td>
                <td className="p-2">{r.recipient || '-'}</td>
                <td className="p-2">{r.country || '-'}</td>
                <td className="p-2">{r.cluster || '-'}</td>
                <td className="p-2 text-right">{r.amount?.toLocaleString('en-US', { maximumFractionDigits: 0 }) || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
