import type { Metadata } from "next";
import { Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { ToastProvider } from "@/contexts/ToastContext";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import Navbar from "@/components/Navbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space",
});

export const metadata: Metadata = {
  title: "AstraRAG - AI-Powered Document Retrieval & Q&A",
  description: "Revolutionary RAG system for document processing, question-answering, and knowledge retrieval using FastAPI, LangChain, and advanced AI technologies.",
  keywords: ["AstraRAG", "AI RAG", "document retrieval", "LLM", "question answering", "knowledge management", "FastAPI", "LangChain"],
  authors: [{ name: "AstraRAG Team" }],
  creator: "AstraRAG",
  publisher: "AstraRAG",
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  openGraph: {
    title: "AstraRAG - AI-Powered Document Retrieval & Q&A",
    description: "Revolutionary RAG system for document processing, question-answering, and knowledge retrieval using cutting-edge AI technologies.",
    type: "website",
    locale: "en_US",
    siteName: "AstraRAG",
    images: [
      {
        url: "/og-image.jpg",
        width: 1200,
        height: 630,
        alt: "AstraRAG - AI-Powered Document Retrieval & Q&A",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "AstraRAG - AI-Powered Document Retrieval & Q&A",
    description: "Revolutionary RAG system for document processing, question-answering, and knowledge retrieval using cutting-edge AI technologies.",
    images: ["/og-image.jpg"],
    creator: "@astrarag",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: "your-google-site-verification-code",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${spaceGrotesk.variable} font-sans antialiased bg-black text-white min-h-screen`}>
        <ErrorBoundary>
          <ToastProvider>
            <AuthProvider>
              <WebSocketProvider>
                <Navbar />
                <main className="pt-16">
                  {children}
                </main>
              </WebSocketProvider>
            </AuthProvider>
          </ToastProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
