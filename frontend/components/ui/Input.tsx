import React from 'react'

type Props = React.InputHTMLAttributes<HTMLInputElement>

export default function Input(props: Props){
  return (
    <input
      className="w-full px-3 py-2 rounded-md bg-slate-800 text-slate-100 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-primary"
      {...props}
    />
  )
}
