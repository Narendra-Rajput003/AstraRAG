'use client';

import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import io from 'socket.io-client';
import { useAuth } from './AuthContext';

interface WebSocketContextType {
  socket: ReturnType<typeof io> | null;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const { user } = useAuth();
  const socketRef = useRef<ReturnType<typeof io> | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const connect = () => {
    if (socketRef.current?.connected) return;

    const token = localStorage.getItem('access_token');
    if (!token || !user) return;

    const socket = io(process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000', {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
    });

    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    });

    socket.on('connect_error', (error: Error) => {
      console.error('WebSocket connection error:', error);
      setIsConnected(false);
    });

    socketRef.current = socket;
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
      setIsConnected(false);
    }
  };

  useEffect(() => {
    if (user) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [user]);

  const value: WebSocketContextType = {
    socket: socketRef.current,
    isConnected,
    connect,
    disconnect,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};