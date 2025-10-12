'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, Tokens } from '@/types';
import { authAPI } from '@/services/api';

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('access_token');
    if (token) {
      // Validate token by making a request that requires auth
      validateToken();
    } else {
      setIsLoading(false);
    }
  }, []);

  const validateToken = async () => {
    const token = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      // First check if token is locally expired
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;

      // If token is expired, try to refresh
      if (payload.exp < currentTime) {
        if (refreshToken) {
          try {
            const refreshResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/refresh`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (refreshResponse.ok) {
              const refreshData = await refreshResponse.json();
              localStorage.setItem('access_token', refreshData.access_token);
              // Validate the new token with server
              await validateTokenWithServer(refreshData.access_token);
            } else {
              throw new Error('Refresh failed');
            }
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError);
            logout();
            return;
          }
        } else {
          logout();
          return;
        }
      } else {
        // Token not expired locally, validate with server
        await validateTokenWithServer(token);
      }
    } catch (error) {
      console.error('Token validation error:', error);
      logout();
    } finally {
      setIsLoading(false);
    }
  };

  const validateTokenWithServer = async (token: string) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/validate`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUser({
          user_id: data.user.user_id,
          username: data.user.email,
          role: data.user.role,
          organization_id: 1,
        });
      } else {
        throw new Error('Token validation failed');
      }
    } catch (error) {
      console.error('Server token validation error:', error);
      throw error;
    }
  };

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      setUser(response.user);
      localStorage.setItem('access_token', response.tokens.access_token);
      localStorage.setItem('refresh_token', response.tokens.refresh_token);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    authAPI.logout();
  };

  const value: AuthContextType = {
    user,
    login,
    logout,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};