import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, ChatSession, LearningProgress, LearningStats } from '../types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string) => void;
  logout: () => void;
}

interface ChatState {
  sessions: ChatSession[];
  currentSessionId: string | null;
  isLoading: boolean;
  createSession: (title: string) => void;
  setCurrentSession: (id: string) => void;
  addMessage: (sessionId: string, message: { role: string; content: string }) => void;
  deleteSession: (id: string) => void;
  setLoading: (loading: boolean) => void;
}

interface LearningState {
  progress: LearningProgress[];
  stats: LearningStats | null;
  isLoading: boolean;
  setProgress: (progress: LearningProgress[]) => void;
  setStats: (stats: LearningStats) => void;
  updateLessonProgress: (courseId: string, lessonId: string) => void;
  setLoading: (loading: boolean) => void;
}

// Auth Store
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    { name: 'auth-storage' }
  )
);

// Chat Store
export const useChatStore = create<ChatState>((set) => ({
  sessions: [],
  currentSessionId: null,
  isLoading: false,
  createSession: (title) =>
    set((state) => {
      const newSession: ChatSession = {
        id: Date.now().toString(),
        title,
        messages: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      return {
        sessions: [newSession, ...state.sessions],
        currentSessionId: newSession.id,
      };
    }),
  setCurrentSession: (id) => set({ currentSessionId: id }),
  addMessage: (sessionId, message) =>
    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === sessionId
          ? {
              ...session,
              messages: [
                ...session.messages,
                {
                  id: Date.now().toString(),
                  role: message.role as 'user' | 'assistant' | 'system',
                  content: message.content,
                  createdAt: new Date().toISOString(),
                },
              ],
              updatedAt: new Date().toISOString(),
            }
          : session
      ),
    })),
  deleteSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      currentSessionId: state.currentSessionId === id ? null : state.currentSessionId,
    })),
  setLoading: (loading) => set({ isLoading: loading }),
}));

// Learning Store
export const useLearningStore = create<LearningState>((set) => ({
  progress: [],
  stats: null,
  isLoading: false,
  setProgress: (progress) => set({ progress }),
  setStats: (stats) => set({ stats }),
  updateLessonProgress: (courseId, _lessonId) =>
    set((state) => ({
      progress: state.progress.map((p) =>
        p.courseId === courseId
          ? {
              ...p,
              completedLessons: p.completedLessons + 1,
              progress: Math.round(((p.completedLessons + 1) / p.totalLessons) * 100),
              lastLearnedAt: new Date().toISOString(),
            }
          : p
      ),
    })),
  setLoading: (loading) => set({ isLoading: loading }),
}));
