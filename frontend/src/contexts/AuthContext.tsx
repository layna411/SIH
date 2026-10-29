import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: any) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  hasRole: (allowedRoles: UserRole[]) => boolean;
  setAuthSession: (token: string, user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem('eduresolve_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('eduresolve_token');
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('eduresolve_token');
      if (storedToken) {
        try {
          const freshUser = await api.get<User>('/auth/me');
          setUser(freshUser);
          localStorage.setItem('eduresolve_user', JSON.stringify(freshUser));
        } catch {
          // Token invalid or expired
          logout();
        }
      }
      setIsLoading(false);
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string): Promise<User> => {
    setIsLoading(true);
    try {
      const res = await api.post<{ access_token: string; user: User }>('/auth/login', {
        email,
        password,
      });

      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem('eduresolve_token', res.access_token);
      localStorage.setItem('eduresolve_user', JSON.stringify(res.user));
      return res.user;
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (payload: any): Promise<User> => {
    setIsLoading(true);
    try {
      const newUser = await api.post<User>('/auth/register', payload);
      // Automatically log in
      return await login(payload.email, payload.password);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('eduresolve_token');
    localStorage.removeItem('eduresolve_user');
  };

  const refreshUser = async () => {
    if (token) {
      try {
        const freshUser = await api.get<User>('/auth/me');
        setUser(freshUser);
        localStorage.setItem('eduresolve_user', JSON.stringify(freshUser));
      } catch {
        logout();
      }
    }
  };

  const hasRole = (allowedRoles: UserRole[]): boolean => {
    if (!user) return false;
    if (user.default_role === 'SUPER_ADMIN') return true;
    if (allowedRoles.includes(user.default_role)) return true;
    
    // Check institutional memberships
    const memberRoles = user.memberships?.map((m) => m.role) || [];
    return memberRoles.some((r) => allowedRoles.includes(r));
  };

  const setAuthSession = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    localStorage.setItem('eduresolve_token', newToken);
    localStorage.setItem('eduresolve_user', JSON.stringify(newUser));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
        hasRole,
        setAuthSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
