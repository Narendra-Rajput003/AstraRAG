import React from 'react'

export default function Avatar({ name, size = 8 }: { name?: string; size?: number }){
  const initials = name ? name.split(' ').map(s=>s[0]).join('').slice(0,2).toUpperCase() : 'AI'
  return (
    <div className={`w-${size} h-${size} rounded-full bg-slate-700 flex items-center justify-center text-sm`}>{initials}</div>
  )
}
