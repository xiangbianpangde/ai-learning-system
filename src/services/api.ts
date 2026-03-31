import axios from 'axios';
import type {
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  LearningProgress,
  LearningStats,
  ChatMessage,
  Course,
  Exercise,
  ExerciseResult,
} from '../types';

// API 基础配置
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============ 用户认证 ============
export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post<AuthResponse>('/auth/register', data);
    return response.data;
  },

  getProfile: async (): Promise<AuthResponse['user']> => {
    const response = await api.get<AuthResponse['user']>('/auth/profile');
    return response.data;
  },

  updateProfile: async (data: Partial<AuthResponse['user']>): Promise<AuthResponse['user']> => {
    const response = await api.put<AuthResponse['user']>('/auth/profile', data);
    return response.data;
  },
};

// ============ 学习数据 ============
export const learningApi = {
  getProgress: async (): Promise<LearningProgress[]> => {
    const response = await api.get<LearningProgress[]>('/learning/progress');
    return response.data;
  },

  getStats: async (): Promise<LearningStats> => {
    const response = await api.get<LearningStats>('/learning/stats');
    return response.data;
  },

  updateProgress: async (courseId: string, lessonId: string): Promise<void> => {
    await api.post('/learning/progress', { courseId, lessonId });
  },
};

// ============ AI 对话 ============
export const chatApi = {
  sendMessage: async (sessionId: string, content: string): Promise<ChatMessage> => {
    const response = await api.post<ChatMessage>('/chat/send', { sessionId, content });
    return response.data;
  },

  getSessions: async (): Promise<{ id: string; title: string; updatedAt: string }[]> => {
    const response = await api.get('/chat/sessions');
    return response.data;
  },

  getSession: async (sessionId: string): Promise<{ messages: ChatMessage[] }> => {
    const response = await api.get(`/chat/sessions/${sessionId}`);
    return response.data;
  },

  createSession: async (title: string): Promise<{ id: string }> => {
    const response = await api.post('/chat/sessions', { title });
    return response.data;
  },

  deleteSession: async (sessionId: string): Promise<void> => {
    await api.delete(`/chat/sessions/${sessionId}`);
  },
};

// ============ 课程内容 ============
export const courseApi = {
  getCourses: async (): Promise<Course[]> => {
    const response = await api.get<Course[]>('/courses');
    return response.data;
  },

  getCourse: async (courseId: string): Promise<Course> => {
    const response = await api.get<Course>(`/courses/${courseId}`);
    return response.data;
  },

  getLesson: async (courseId: string, lessonId: string): Promise<Course['lessons'][0]> => {
    const response = await api.get(`/courses/${courseId}/lessons/${lessonId}`);
    return response.data;
  },
};

// ============ 练习系统 ============
export const exerciseApi = {
  getExercise: async (exerciseId: string): Promise<Exercise> => {
    const response = await api.get<Exercise>(`/exercises/${exerciseId}`);
    return response.data;
  },

  submitExercise: async (exerciseId: string, answer: string): Promise<ExerciseResult> => {
    const response = await api.post<ExerciseResult>('/exercises/submit', { exerciseId, answer });
    return response.data;
  },

  getExerciseHistory: async (lessonId: string): Promise<ExerciseResult[]> => {
    const response = await api.get<ExerciseResult[]>(`/exercises/history/${lessonId}`);
    return response.data;
  },
};

export default api;
