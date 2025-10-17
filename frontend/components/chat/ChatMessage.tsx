import React from 'react'

export default function ChatMessage({ role, text }: { role: 'user'|'assistant'; text: string }){
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} my-2`}> 
      <div className={`${isUser ? 'bg-slate-700 text-white' : 'bg-slate-800 text-slate-100'} px-4 py-2 rounded-lg max-w-[80%]`}>{text}</div>
    </div>
  )
}
