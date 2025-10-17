# AstraRAG Frontend

This folder contains a Next.js 14 TypeScript frontend for AstraRAG.

Quick start

1. Install dependencies

```powershell
cd frontend; npm install
```

2. Run development server

```powershell
npm run dev
```

By default the frontend expects the API gateway at `http://localhost:8000`. You can override with `NEXT_PUBLIC_API_BASE`.

Notes

- Chat streaming is implemented using fetch + ReadableStream in `components/chat/ChatShell.tsx` and proxies to `/search/ask` on the API gateway.
- This scaffold focuses on micro-components and a composable chat UI. Continue by adding auth flows, uploads, analytics, and improved animations.
