import create from 'zustand'

type Message = { id: string; role: 'user'|'assistant'; text: string }

type State = {
  token?: string | null
  setToken: (t?: string|null)=>void
  messages: Message[]
  addMessage: (m: Message)=>void
  clearMessages: ()=>void
}

export const useStore = create<State>((set)=>({
  token: null,
  setToken: (t)=>set({ token: t }),
  messages: [],
  addMessage: (m)=>set(s=>({ messages: [...s.messages, m] })),
  clearMessages: ()=>set({ messages: [] })
}))
