"use client"
import React, { useState, useRef } from 'react'
import ChatMessage from './ChatMessage'
import Input from '../ui/Input'
import Button from '../ui/Button'

type Message = { id: string; role: 'user'|'assistant'; text: string }

async function streamQuery(query: string, onChunk: (s: string)=>void){
  const base = (process.env.NEXT_PUBLIC_API_BASE as string) || 'http://localhost:8000'
  const res = await fetch(`${base}/search/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })

  if (!res.ok) throw new Error('Network response not ok')

  const reader = res.body?.getReader()
  if (!reader) {
    const text = await res.text()
    onChunk(text)
    return
  }

  const decoder = new TextDecoder()
  while(true){
    const { done, value } = await reader.read()
    if (done) break
    onChunk(decoder.decode(value))
  }
}

export default function ChatShell(){
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const assistantBuffer = useRef('')

  const send = async () => {
    if (!input.trim()) return
    const userMsg: Message = { id: Date.now().toString(), role: 'user', text: input }
    setMessages(m => [...m, userMsg])
    setInput('')
    setLoading(true)

    const assistantId = Date.now().toString() + '-a'
    const assistantMsg: Message = { id: assistantId, role: 'assistant', text: '' }
    setMessages(m => [...m, assistantMsg])

    try{
      await streamQuery(userMsg.text, (chunk)=>{
        assistantBuffer.current += chunk
        setMessages(m => m.map(msg => msg.id === assistantId ? { ...msg, text: assistantBuffer.current } : msg))
      })
    }catch(err:any){
      setMessages(m => [...m, { id: Date.now().toString()+'-err', role: 'assistant', text: `Error: ${err.message}` }])
    }finally{
      setLoading(false)
      assistantBuffer.current = ''
    }
  }

  return (
    <div className="bg-gradient-to-br from-slate-900/60 to-slate-800/40 rounded-xl p-4 shadow-lg">
      <div className="h-[60vh] overflow-auto p-2">
        {messages.map(m => <ChatMessage key={m.id} role={m.role} text={m.text} />)}
      </div>

      <div className="mt-4 flex gap-2">
        <Input placeholder="Ask something..." value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{ if(e.key==='Enter') send() }} />
        <Button onClick={send} disabled={loading}>{loading ? 'Thinking...' : 'Send'}</Button>
      </div>
    </div>
  )
}
