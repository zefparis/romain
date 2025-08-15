const baseURL = import.meta.env.VITE_API_URL || ''

async function http(path, { method = 'GET', body, headers } = {}) {
  const res = await fetch(`${baseURL}${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', ...(headers || {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const api = {
  listConversations: () => http('/api/conversations'),
  createConversation: (title) => http('/api/conversations', { method: 'POST', body: { title } }),
  getMessages: (id) => http(`/api/conversations/${id}/messages`),
  sendMessage: ({ conversation_id, message }) => http('/api/chat', { method: 'POST', body: { conversation_id, message } }),
  streamComplete: async ({ message, onToken }) => {
    const res = await fetch(`${baseURL}/api/chat/complete/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    })
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`)
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let idx
      while ((idx = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, idx).trim()
        buffer = buffer.slice(idx + 2)
        if (!frame.startsWith('data:')) continue
        const payload = frame.slice(5).trim()
        if (payload === '[DONE]') return
        if (payload.startsWith('[ERROR]')) throw new Error(payload)
        onToken?.(payload)
      }
    }
  },
  uploadFiles: async (files) => {
    const form = new FormData()
    for (const f of files) form.append('files', f)
    const res = await fetch(`${baseURL}/api/docs/upload`, { method: 'POST', body: form })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.json()
  },
  // Upload a single file with progress callback (0..1) and abort support
  uploadFileWithProgress: (file, onProgress) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${baseURL}/api/docs/upload`)
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress?.(e.loaded / e.total)
    }
    const promise = new Promise((resolve, reject) => {
      xhr.onreadystatechange = () => {
        if (xhr.readyState === 4) {
          if (xhr.status >= 200 && xhr.status < 300) {
            try { resolve(JSON.parse(xhr.responseText)) } catch (e) { resolve({}) }
          } else if (xhr.status === 0) {
            // Aborted
            reject(new Error('aborted'))
          } else {
            reject(new Error(`HTTP ${xhr.status}`))
          }
        }
      }
    })
    const form = new FormData()
    form.append('files', file)
    xhr.send(form)
    return { promise, abort: () => xhr.abort() }
  },
  listFiles: () => http('/api/docs/files'),
  downloadFile: async (name) => {
    const res = await fetch(`${baseURL}/api/docs/files/${encodeURIComponent(name)}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    return res.blob()
  },
  // Google Drive integrations
  gdrive: {
    loginUrl: () => `${baseURL}/api/integrations/google/auth`,
    list: async (q='') => http(`/api/integrations/google/list${q?`?q=${encodeURIComponent(q)}`:''}`),
    import: async (id) => http(`/api/integrations/google/import`, { method:'POST', body: { id } }),
  },
  onedrive: {
    loginUrl: () => `${baseURL}/api/integrations/onedrive/auth`,
    list: async (q='') => http(`/api/integrations/onedrive/list${q?`?q=${encodeURIComponent(q)}`:''}`),
    import: async (id) => http(`/api/integrations/onedrive/import`, { method:'POST', body: { id } }),
  }
  ,
  humdata: {
    crises: (params={}) => {
      const q = new URLSearchParams(params).toString()
      return http(`/api/humdata/crises${q?`?${q}`:''}`)
    },
    jobs: (params={}) => {
      const q = new URLSearchParams(params).toString()
      return http(`/api/humdata/jobs${q?`?${q}`:''}`)
    },
    funding: (params={}) => {
      const q = new URLSearchParams(params).toString()
      return http(`/api/humdata/funding${q?`?${q}`:''}`)
    },
  }
}
