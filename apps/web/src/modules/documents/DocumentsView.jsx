import React, { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../../lib/api'

export default function DocumentsView(){
  const fileRef = useRef(null)
  const [downloading, setDownloading] = useState(false)

  // Exports handled by backend templates routes
  async function exportDoc(kind){
    setDownloading(true)
    try {
      const res = await fetch(`/api/docs/export/${kind}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: {
            text: 'Bonjour Romain — ceci est un exemple de document généré.' ,
            rows: [ { Nom:'Alice', Score: 92 }, { Nom:'Bob', Score: 85 } ]
          }
        })
      })
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `export.${kind==='pdf'?'pdf': kind==='docx'?'docx':'xlsx'}`
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } finally { setDownloading(false) }
  }

  const [files, setFiles] = useState([])
  const [dragOver, setDragOver] = useState(false)
  const [queue, setQueue] = useState([]) // [{name, progress, abort}]
  const [preview, setPreview] = useState(null) // {name, url}
  const [gConnected, setGConnected] = useState(false)
  const [gItems, setGItems] = useState([])
  const [gQuery, setGQuery] = useState('')
  const [odConnected, setOdConnected] = useState(false)
  const [odItems, setOdItems] = useState([])
  const [odQuery, setOdQuery] = useState('')
  async function refresh(){
    const j = await api.listFiles()
    setFiles(j.files || [])
  }

  useEffect(()=>{ refresh() }, [])
  useEffect(()=>{
    // detect hash after OAuth redirect
    if (window.location.hash.includes('gdrive=connected')){
      setGConnected(true)
      window.location.hash = ''
    }
    if (window.location.hash.includes('onedrive=connected')){
      setOdConnected(true)
      window.location.hash = ''
    }
  }, [])

  function openPicker(){ fileRef.current?.click() }
  async function handleUploadList(sel){
    // Start each upload, capture its abort handle
    const tasks = sel.map(f => {
      const { promise, abort } = api.uploadFileWithProgress(f, (p)=>{
        setQueue(q => q.map(t => t.name===f.name? {...t, progress: p}: t))
      })
      return { name: f.name, progress: 0, abort, promise }
    })
    setQueue(q => [...q, ...tasks])
    // Await all (errors for aborted are ignored)
    await Promise.allSettled(tasks.map(t => t.promise))
    setQueue(q => q.filter(t => t.progress < 1))
    await refresh()
  }
  function cancelAll(){
    setQueue(q => {
      q.forEach(t => t.abort?.())
      return []
    })
  }
  async function onFiles(e){
    const sel = Array.from(e.target.files || [])
    if (!sel.length) return
    handleUploadList(sel)
  }

  const onDragOver = (e)=>{ e.preventDefault(); setDragOver(true) }
  const onDragLeave = ()=> setDragOver(false)
  const onDrop = (e)=>{
    e.preventDefault(); setDragOver(false)
    const sel = Array.from(e.dataTransfer.files || [])
    if (!sel.length) return
    handleUploadList(sel)
  }

  async function download(name){
    const blob = await api.downloadFile(name)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  }

  // PDF preview helpers
  const isPDF = (name)=> name.toLowerCase().endsWith('.pdf')
  async function previewPdf(name){
    const blob = await api.downloadFile(name)
    const url = URL.createObjectURL(blob)
    setPreview({ name, url })
  }
  function closePreview(){
    if (preview?.url) URL.revokeObjectURL(preview.url)
    setPreview(null)
  }

  return (
    <section className="flex-1 flex flex-col">
      <div className="p-4 border-b bg-white">
        <h2 className="font-semibold">Documents</h2>
      </div>
      <div className="p-4 space-y-4">
        <div className="flex flex-wrap gap-2 items-center">
          <button onClick={()=>exportDoc('pdf')} disabled={downloading} className="px-3 py-2 rounded bg-black text-white disabled:opacity-50">Exporter PDF</button>
          <button onClick={()=>exportDoc('docx')} disabled={downloading} className="px-3 py-2 rounded bg-black text-white disabled:opacity-50">Exporter DOCX</button>
          <button onClick={()=>exportDoc('xlsx')} disabled={downloading} className="px-3 py-2 rounded bg-black text-white disabled:opacity-50">Exporter XLSX</button>
          <div className="flex-1 min-w-[1rem]" />
          <a href={api.gdrive.loginUrl()} className="px-3 py-2 rounded bg-green-700 text-white whitespace-nowrap">{gConnected? 'Google Drive connecté': 'Connecter Google Drive'}</a>
          <a href={api.onedrive.loginUrl()} className="px-3 py-2 rounded bg-blue-700 text-white whitespace-nowrap">{odConnected? 'OneDrive connecté': 'Connecter OneDrive'}</a>
        </div>

        <div className={`border rounded p-4 bg-white ${dragOver? 'ring-2 ring-blue-500': ''}`} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div>
              <div className="font-medium">Téléverser des fichiers</div>
              <div className="text-sm text-slate-500">PDF, Word, Excel, etc.</div>
            </div>

          <div className="mt-6">
            <div className="flex items-center gap-2 mb-2">
              <div className="text-sm font-medium">OneDrive</div>
              {odConnected ? (
                <span className="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700">Connecté</span>
              ) : (
                <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600">Non connecté</span>
              )}
              <div className="flex-1" />
              <input value={odQuery} onChange={e=>setOdQuery(e.target.value)} placeholder="Rechercher..." className="border rounded px-2 py-1 text-sm" />
              <button disabled={!odConnected} onClick={async()=>{ const r=await api.onedrive.list(odQuery); setOdItems(r.files||[]) }} className="text-sm px-2 py-1 rounded bg-slate-800 text-white disabled:opacity-50">Lister</button>
            </div>
            <ul className="divide-y">
              {odItems.map(it=> (
                <li key={it.id} className="py-2 flex items-center justify-between">
                  <div className="text-sm">{it.name} <span className="text-xs text-slate-500">{it.mimeType}</span></div>
                  <div className="flex gap-2">
                    <button onClick={async()=>{ await api.onedrive.import(it.id); await refresh() }} className="text-sm px-2 py-1 rounded bg-blue-600 text-white">Importer</button>
                  </div>
                </li>
              ))}
              {odConnected && odItems.length===0 && <li className="py-2 text-sm text-slate-500">Aucun fichier. Lance une recherche ou clique Lister.</li>}
              {!odConnected && <li className="py-2 text-sm text-slate-500">Connecte OneDrive pour lister et importer des fichiers.</li>}
            </ul>
          </div>
            <div>
              <input ref={fileRef} type="file" multiple className="hidden" onChange={onFiles} />
              <button onClick={openPicker} className="px-3 py-2 rounded bg-slate-800 text-white">Choisir des fichiers</button>
            </div>
          </div>
          <div className="text-xs text-slate-500 mt-2">Astuce: Glisser-déposer des fichiers ici pour les importer. Les envois en cours s’affichent ci-dessous.</div>
          {queue.length>0 && (
            <div className="mt-3">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-2 mb-2">
                <div className="text-sm font-medium">Envois en cours</div>
                <button onClick={cancelAll} className="text-xs px-2 py-1 rounded bg-red-600 text-white">Annuler tout</button>
              </div>
              <ul className="space-y-2">
                {queue.map(t=> (
                  <li key={t.name} className="text-sm">
                    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
                      <span className="truncate mr-2 max-w-full">{t.name}</span>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-xs text-slate-500">{Math.round((t.progress||0)*100)}%</span>
                        <button onClick={()=>{ t.abort?.(); setQueue(q=>q.filter(x=>x.name!==t.name)) }} className="text-xs px-2 py-1 rounded bg-red-600 text-white">Annuler</button>
                      </div>
                    </div>
                    <div className="h-2 bg-slate-200 rounded overflow-hidden">
                      <div className="h-full bg-blue-600" style={{ width: `${(t.progress||0)*100}%` }} />
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="mt-4">
            <div className="text-sm font-medium mb-2">Fichiers:</div>
            <ul className="divide-y">
              {files.map(f=> (
                <li key={f.name} className="py-2 flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
                  <div className="text-sm break-words max-w-full">{f.name} <span className="text-xs text-slate-500">({f.size} o)</span></div>
                  <div className="flex gap-2 flex-wrap">
                    {isPDF(f.name) && <button onClick={()=>previewPdf(f.name)} className="text-sm px-2 py-1 rounded bg-slate-700 text-white">Prévisualiser</button>}
                    <button onClick={()=>download(f.name)} className="text-sm px-2 py-1 rounded bg-black text-white">Télécharger</button>
                  </div>
                </li>
              ))}
              {files.length===0 && <li className="py-2 text-sm text-slate-500">Aucun fichier pour le moment.</li>}
            </ul>
          </div>

          <div className="mt-6">
            <div className="flex flex-col md:flex-row items-start md:items-center gap-2 mb-2">
              <div className="text-sm font-medium">Google Drive</div>
              {gConnected ? (
                <span className="text-xs px-2 py-1 rounded bg-emerald-100 text-emerald-700">Connecté</span>
              ) : (
                <span className="text-xs px-2 py-1 rounded bg-slate-100 text-slate-600">Non connecté</span>
              )}
              <div className="flex-1" />
              <input value={gQuery} onChange={e=>setGQuery(e.target.value)} placeholder="Rechercher..." className="border rounded px-2 py-1 text-sm w-full md:w-auto" />
              <button disabled={!gConnected} onClick={async()=>{ const r=await api.gdrive.list(gQuery); setGItems(r.files||[]) }} className="text-sm px-2 py-1 rounded bg-slate-800 text-white disabled:opacity-50">Lister</button>
            </div>
            <ul className="divide-y">
              {gItems.map(it=> (
                <li key={it.id} className="py-2 flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
                  <div className="text-sm break-words max-w-full">{it.name} <span className="text-xs text-slate-500">{it.mimeType}</span></div>
                  <div className="flex gap-2 flex-wrap">
                    <button onClick={async()=>{ await api.gdrive.import(it.id); await refresh() }} className="text-sm px-2 py-1 rounded bg-blue-600 text-white">Importer</button>
                  </div>
                </li>
              ))}
              {gConnected && gItems.length===0 && <li className="py-2 text-sm text-slate-500">Aucun fichier. Lance une recherche ou clique Lister.</li>}
              {!gConnected && <li className="py-2 text-sm text-slate-500">Connecte Google Drive pour lister et importer des fichiers.</li>}
            </ul>
          </div>
        </div>

        {preview && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={closePreview}>
            <div className="bg-white w-[90vw] h-[90vh] rounded shadow-lg overflow-hidden" onClick={e=>e.stopPropagation()}>
              <div className="p-2 border-b flex items-center justify-between">
                <div className="font-medium text-sm">Prévisualisation: {preview.name}</div>
                <button onClick={closePreview} className="px-2 py-1 text-sm bg-slate-800 text-white rounded">Fermer</button>
              </div>
              <iframe title="PDF Preview" src={preview.url} className="w-full h-full" />
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
