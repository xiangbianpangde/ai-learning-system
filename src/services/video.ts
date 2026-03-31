/**
 * 视频生成服务 - 教学视频生成 (FFmpeg + ElevenLabs)
 * 规格：1080p/30fps、音频清晰度≥90%
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export interface VideoGenerationRequest {
  title: string;
  script: string;
  voiceId?: string;
  slides?: SlideConfig[];
  outputFormat?: 'mp4' | 'webm';
}

export interface SlideConfig {
  duration: number; // seconds
  title: string;
  content: string;
  backgroundImage?: string;
  highlight?: string[];
}

export interface VideoGenerationResponse {
  jobId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  videoUrl?: string;
  thumbnailUrl?: string;
  duration?: number;
  resolution?: string;
  errorMessage?: string;
}

export interface VoiceConfig {
  id: string;
  name: string;
  language: string;
  gender: 'male' | 'female';
  style: string;
}

/**
 * 可用的语音列表
 */
export const AVAILABLE_VOICES: VoiceConfig[] = [
  { id: 'zh-CN-standard-1', name: '晓晓 (女)', language: 'zh-CN', gender: 'female', style: 'warm' },
  { id: 'zh-CN-standard-2', name: '云希 (男)', language: 'zh-CN', gender: 'male', style: 'professional' },
  { id: 'zh-CN-standard-3', name: '云扬 (男)', language: 'zh-CN', gender: 'male', style: 'friendly' },
  { id: 'en-US-standard-1', name: 'Emma (F)', language: 'en-US', gender: 'female', style: 'clear' },
  { id: 'en-US-standard-2', name: 'Brian (M)', language: 'en-US', gender: 'male', style: 'authoritative' },
];

/**
 * 创建视频生成任务
 */
export async function createVideoTask(request: VideoGenerationRequest): Promise<{ jobId: string }> {
  const response = await axios.post(`${API_BASE}/video/generate`, request);
  return response.data;
}

/**
 * 查询视频生成进度
 */
export async function getVideoStatus(jobId: string): Promise<VideoGenerationResponse> {
  const response = await axios.get(`${API_BASE}/video/status/${jobId}`);
  return response.data;
}

/**
 * 使用 ElevenLabs 生成音频
 */
export async function generateAudioWithElevenLabs(
  text: string,
  voiceId: string = 'zh-CN-standard-1'
): Promise<{ audioUrl: string; duration: number }> {
  const response = await axios.post(
    `${API_BASE}/video/tts`,
    { text, voiceId },
    { responseType: 'arraybuffer' }
  );
  
  // 返回音频 Blob URL 和时长
  const blob = new Blob([response.data], { type: 'audio/mpeg' });
  const audioUrl = URL.createObjectURL(blob);
  const duration = parseFloat(response.headers['x-audio-duration'] || '0');
  
  return { audioUrl, duration };
}

/**
 * 使用 FFmpeg 合成视频 (前端模拟，实际由后端处理)
 */
export async function synthesizeVideo(
  audioUrl: string,
  slides: SlideConfig[]
): Promise<{ jobId: string }> {
  const response = await axios.post(`${API_BASE}/video/synthesize`, {
    audioUrl,
    slides,
    output: {
      resolution: '1920x1080',
      fps: 30,
      format: 'mp4',
      audioQuality: 'high', // ≥90% clarity
    },
  });
  return response.data;
}

/**
 * 下载生成的视频
 */
export async function downloadVideo(jobId: string): Promise<Blob> {
  const response = await axios.get(`${API_BASE}/video/download/${jobId}`, {
    responseType: 'blob',
  });
  return response.data;
}

/**
 * 验证音频清晰度 (通过后端分析)
 */
export async function validateAudioClarity(audioUrl: string): Promise<{
  clarity: number;
  snr: number;
  passed: boolean;
}> {
  const response = await axios.post(`${API_BASE}/video/validate-audio`, { audioUrl });
  return response.data;
}

export default {
  createVideoTask,
  getVideoStatus,
  generateAudioWithElevenLabs,
  synthesizeVideo,
  downloadVideo,
  validateAudioClarity,
  AVAILABLE_VOICES,
};
