import ChatShell from '../components/chat/ChatShell'

export default function Page(){
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-semibold mb-4">AstraRAG — Assistant</h1>
      <ChatShell />
    </div>
  )
}
