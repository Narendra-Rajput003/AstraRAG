import './globals.css'
import { ReactNode } from 'react'

export const metadata = {
  title: 'AstraRAG',
  description: 'Frontend for AstraRAG'
}

export default function RootLayout({ children }: { children: ReactNode }){
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen flex items-stretch">
          <main className="flex-1 p-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  )
}
