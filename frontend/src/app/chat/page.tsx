'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import Chat from '@/components/Chat';
import { useRouter } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';

export default function ChatPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!user) {
    router.push('/login');
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gray-800 border-b border-gray-700 px-4 py-4"
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/">
              <motion.button
                className="p-2 text-gray-400 hover:text-white transition-colors"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                <ArrowLeft className="h-5 w-5" />
              </motion.button>
            </Link>
            <div>
              <h1 className="text-xl font-semibold text-white">Document Chat</h1>
              <p className="text-sm text-gray-400">
                Ask questions about your uploaded documents
              </p>
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-400">Welcome,</div>
            <div className="text-white font-medium">{user.username}</div>
          </div>
        </div>
      </motion.header>

      {/* Chat Interface */}
      <motion.main
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="h-[calc(100vh-80px)]"
      >
        <Chat />
      </motion.main>
    </div>
  );
}