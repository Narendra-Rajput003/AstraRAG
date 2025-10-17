import React from 'react'

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'ghost' }

export default function Button({ variant = 'primary', className = '', ...props }: Props){
  const base = 'px-4 py-2 rounded-md font-medium transition-colors '
  const styles = variant === 'primary'
    ? 'bg-primary text-white hover:bg-indigo-600'
    : 'bg-transparent text-slate-200 hover:bg-slate-700'
  return <button className={`${base} ${styles} ${className}`} {...props} />
}
