// 用户类型
export interface User {
  id: string;
  username: string;
  email: string;
  avatar?: string;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

// 学习进度类型
export interface LearningProgress {
  courseId: string;
  courseName: string;
  progress: number; // 0-100
  lastLearnedAt: string;
  totalLessons: number;
  completedLessons: number;
}

export interface LearningStats {
  totalLearningTime: number; // minutes
  coursesCompleted: number;
  exercisesCompleted: number;
  averageScore: number;
  streakDays: number;
  weeklyActivity: number[]; // 7 days
}

// AI 对话类型
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
}

export interface ChatSession {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

// 课程类型
export interface Course {
  id: string;
  title: string;
  description: string;
  thumbnail?: string;
  lessons: Lesson[];
  progress: number;
}

export interface Lesson {
  id: string;
  title: string;
  type: 'video' | 'text' | 'exercise';
  content: string;
  videoUrl?: string;
  duration?: number; // seconds
  completed: boolean;
}

// 练习类型
export interface Exercise {
  id: string;
  lessonId: string;
  type: 'multiple-choice' | 'fill-blank' | 'code';
  question: string;
  options?: string[];
  correctAnswer: string | string[];
  explanation: string;
}

export interface ExerciseSubmission {
  exerciseId: string;
  answer: string;
  isCorrect: boolean;
  submittedAt: string;
}

export interface ExerciseResult {
  isCorrect: boolean;
  score: number;
  feedback: string;
  correctAnswer?: string;
}
