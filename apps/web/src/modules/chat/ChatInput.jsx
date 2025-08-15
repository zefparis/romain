import React, { useEffect, useRef, useState } from 'react'

export default function ChatInput({ onSend, disabled, typing, lastAssistant }){
  const [q,setQ]=useState('Bonjour, prépare un plan de rapport.')
  const [listening, setListening] = useState(false)
  const recRef = useRef(null)
  const videoRef = useRef(null)
  const [camOn, setCamOn] = useState(false)
  const [cams, setCams] = useState([]) // list of video input devices
  const [selectedCamId, setSelectedCamId] = useState('')
  const [resolution, setResolution] = useState('640x480') // default safer resolution
  const [lastError, setLastError] = useState('')

  // Speech Recognition (Web Speech API)
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return
    const rec = new SR()
    rec.lang = 'fr-FR'
    rec.interimResults = true
    rec.continuous = true
    rec.onresult = (e) => {
      let finalTxt = ''
      for (let i= e.resultIndex; i < e.results.length; i++) {
        const res = e.results[i]
        if (res.isFinal) finalTxt += res[0].transcript
      }
      if (finalTxt) setQ(prev => (prev ? (prev.trim() + ' ') : '') + finalTxt.trim())
    }
    rec.onerror = (ev) => {
      setListening(false)
      console.warn('SpeechRecognition error', ev)
      alert('Problème micro: ' + (ev?.error || 'inconnu'))
    }
    rec.onend = () => setListening(false)
    recRef.current = rec
  }, [])

  const toggleMic = () => {
    const rec = recRef.current
    if (!rec) return alert('Reconnaissance vocale non supportée dans ce navigateur')
    if (!listening) { setListening(true); rec.start() } else { rec.stop() }
  }

  // Text To Speech for last assistant message or typing stream
  const speak = () => {
    if (!('speechSynthesis' in window)) {
      alert('Synthèse vocale non supportée dans ce navigateur')
      return
    }
    const text = (typing && typing.length>0) ? typing : (lastAssistant || q || '')
    if (!text) {
      alert('Aucun texte à lire pour le moment')
      return
    }
    window.speechSynthesis.cancel()
    const utt = new SpeechSynthesisUtterance(text)
    utt.lang = 'fr-FR'
    window.speechSynthesis.speak(utt)
  }

  // Camera preview (no streaming, local preview only)
  // Enumerate cameras
  useEffect(() => {
    async function loadDevices() {
      try {
        if (!navigator.mediaDevices?.enumerateDevices) return
        const devices = await navigator.mediaDevices.enumerateDevices()
        const videoInputs = devices.filter(d => d.kind === 'videoinput')
        setCams(videoInputs)
        // Ensure selected device is valid
        if (videoInputs.length) {
          const exists = videoInputs.some(d => d.deviceId === selectedCamId)
          setSelectedCamId(exists ? selectedCamId : (selectedCamId==='auto' ? 'auto' : videoInputs[0].deviceId))
        } else {
          setSelectedCamId('')
        }
      } catch (e) {
        // ignore
      }
    }
    // Just enumerate; do not auto-open camera (prevents locking the device)
    (async () => { await loadDevices() })()
    // update on device changes (USB cam plugged/unplugged)
    try {
      navigator.mediaDevices?.addEventListener?.('devicechange', loadDevices)
    } catch (_) {}
    return () => {
      // stop any running stream when component unmounts
      const stream = videoRef.current?.srcObject
      if (stream) stream.getTracks().forEach(t=>t.stop())
      try {
        navigator.mediaDevices?.removeEventListener?.('devicechange', loadDevices)
      } catch (_) {}
    }
  }, [])

  const stopCamera = () => {
    const stream = videoRef.current?.srcObject
    if (stream) stream.getTracks().forEach(t=>t.stop())
    if (videoRef.current) videoRef.current.srcObject = null
    setCamOn(false)
    setLastError('')
  }

  const startCamera = async () => {
    try {
      setLastError('')
      // stop any existing stream first to free the device
      const existing = videoRef.current?.srcObject
      if (existing) existing.getTracks().forEach(t=>t.stop())

      // Build constraints
      const [w, h] = (resolution || '640x480').split('x').map(n=>parseInt(n,10))
      // Use ideal instead of exact to reduce OverconstrainedError risks
      const base = { width: { ideal: w }, height: { ideal: h }, aspectRatio: { ideal: w / Math.max(h, 1) }, frameRate: { ideal: 30 } }
      const useDevice = selectedCamId && selectedCamId !== 'auto'
      const videoConstraint = useDevice
        ? { deviceId: { exact: selectedCamId }, ...base }
        : base
      let stream
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: videoConstraint, audio: false })
      } catch (err) {
        // Fallback 1: try without deviceId
        try {
          stream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: w }, height: { ideal: h } }, audio: false })
        } catch (err2) {
          // Fallback 2: try facingMode variations (useful on mobiles)
          try {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: false })
          } catch (err3) {
            stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
          }
        }
      }
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        // Ensure play after metadata
        await new Promise((resolve) => {
          const v = videoRef.current
          if (!v) return resolve()
          const handler = async () => {
            v.removeEventListener('loadedmetadata', handler)
            try { await v.play?.() } catch (_) {}
            resolve()
          }
          v.addEventListener('loadedmetadata', handler)
          // if metadata already loaded
          if (v.readyState >= 1) handler()
        })
      }
      setCamOn(true)
      // Diagnostics: log track settings
      const tracks = stream.getVideoTracks?.() || []
      if (!tracks.length) {
        setLastError('Aucune piste vidéo obtenue du périphérique. Essayez un autre périphérique ou une autre résolution.')
        stopCamera()
        return
      }
      const track = tracks[0]
      if (track) {
        const s = track.getSettings?.() || {}
        console.debug('Camera settings:', s)
        // If the track ends (device unplugged), reflect in UI
        track.onended = () => {
          stopCamera()
        }
      }
    } catch (e) {
      console.warn('Camera error', e)
      setLastError(e?.name ? `${e.name}: ${e.message || ''}` : 'Accès caméra refusé ou indisponible')
      setCamOn(false)
    }
  }

  const toggleCamera = async () => {
    if (camOn) return stopCamera()
    await startCamera()
  }

  return (
    <>
      <div className="px-4 pb-2 flex flex-col md:flex-row items-stretch md:items-end gap-3">
        {camOn && (
          <video
            key={selectedCamId || 'default'}
            ref={videoRef}
            autoPlay
            muted
            playsInline
            className="w-full md:w-96 bg-black rounded border object-cover"
            style={{ aspectRatio: '16/9' }}
          />
        )}
        <div className="flex flex-col gap-2 text-sm min-w-0">
          <label className="flex items-center gap-2">
            <span>Caméra:</span>
            <select
              className="border rounded px-2 py-1"
              value={selectedCamId}
              onChange={async (e)=>{
                const id = e.target.value
                setSelectedCamId(id)
                // if camera is running, switch to the newly selected one
                if (camOn) {
                  stopCamera()
                  await startCamera()
                }
              }}
            >
              <option value="auto">Auto (par défaut)</option>
              {cams.length === 0 ? (
                <option value="">(aucune caméra)</option>
              ) : (
                cams.map((c, idx) => (
                  <option key={c.deviceId || idx} value={c.deviceId}>
                    {c.label || `Caméra ${idx+1}`}
                  </option>
                ))
              )}
            </select>
          </label>
          <label className="flex items-center gap-2">
            <span>Résolution:</span>
            <select
              className="border rounded px-2 py-1"
              value={resolution}
              onChange={async (e)=>{
                setResolution(e.target.value)
                if (camOn) {
                  await startCamera()
                }
              }}
            >
              <option value="640x480">640x480</option>
              <option value="1280x720">1280x720 (HD)</option>
              <option value="1920x1080">1920x1080 (Full HD)</option>
            </select>
          </label>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="px-2 py-1 border rounded" onClick={async ()=>{
              try {
                const devices = await navigator.mediaDevices.enumerateDevices()
                const videoInputs = devices.filter(d => d.kind === 'videoinput')
                setCams(videoInputs)
                if (videoInputs.length && !videoInputs.some(d=>d.deviceId===selectedCamId)) {
                  setSelectedCamId(videoInputs[0].deviceId)
                }
              } catch (_) {}
            }}>Rafraîchir</button>
          </div>
          {lastError && (
            <div className="text-red-600 text-xs">{lastError}</div>
          )}
        </div>
      </div>
      <form onSubmit={(e)=>{e.preventDefault(); onSend(q);}} className="p-4 border-t bg-white flex flex-col md:flex-row gap-2 items-stretch md:items-end">
        <div className="flex-1 flex flex-col gap-2 min-w-0">
          <textarea className="w-full p-3 border rounded-lg" rows={3} value={q} onChange={e=>setQ(e.target.value)} placeholder="Votre message..." />
          <div className="flex flex-wrap gap-2 text-sm">
            <button type="button" onClick={toggleMic} className={`px-3 py-1 rounded border ${listening?'bg-green-600 text-white':'bg-white'}`}>{listening?'Stop mic':'Dicter'}</button>
            <button type="button" onClick={speak} className="px-3 py-1 rounded border">Lire la réponse</button>
            <button type="button" onClick={toggleCamera} className={`px-3 py-1 rounded border ${camOn?'bg-slate-200':'bg-white'}`}>{camOn?'Stop caméra':'Caméra'}</button>
          </div>
        </div>
        <button disabled={disabled} className="h-11 md:h-10 w-full md:w-auto px-4 py-2 rounded-lg bg-black text-white disabled:opacity-50">Envoyer</button>
      </form>
    </>
  )
}
