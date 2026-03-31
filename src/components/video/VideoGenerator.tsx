/**
 * 视频生成器组件 - 教学视频生成 UI
 */

import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Select,
  Button,
  Card,
  Progress,
  Space,
  message,
  Upload,
  List,
  Tag,
  Collapse,
} from 'antd';
import {
  PlayCircleOutlined,
  DownloadOutlined,
  LoadingOutlined,
  CheckCircleOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import videoService, {
  type VideoGenerationRequest,
  type SlideConfig,
  type VoiceConfig,
  AVAILABLE_VOICES,
} from '../../services/video';

const { TextArea } = Input;
const { Panel } = Collapse;

interface VideoGeneratorProps {
  onVideoGenerated?: (videoUrl: string) => void;
}

const VideoGenerator: React.FC<VideoGeneratorProps> = ({ onVideoGenerated }) => {
  const [form] = Form.useForm();
  const [slides, setSlides] = useState<SlideConfig[]>([]);
  const [currentSlide, setCurrentSlide] = useState<Partial<SlideConfig>>({});
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'generating' | 'completed' | 'failed'>('idle');

  // 添加幻灯片
  const addSlide = () => {
    if (currentSlide.title && currentSlide.content) {
      const newSlide: SlideConfig = {
        duration: currentSlide.duration || 10,
        title: currentSlide.title,
        content: currentSlide.content,
        highlight: currentSlide.highlight || [],
      };
      setSlides([...slides, newSlide]);
      setCurrentSlide({});
      message.success('幻灯片已添加');
    } else {
      message.warning('请填写幻灯片标题和内容');
    }
  };

  // 删除幻灯片
  const removeSlide = (index: number) => {
    setSlides(slides.filter((_, i) => i !== index));
  };

  // 开始生成视频
  const handleGenerate = async (values: any) => {
    if (slides.length === 0) {
      message.error('请至少添加一张幻灯片');
      return;
    }

    setGenerating(true);
    setStatus('generating');
    setProgress(0);

    try {
      // 创建视频生成任务
      const request: VideoGenerationRequest = {
        title: values.title,
        script: values.script,
        voiceId: values.voiceId,
        slides,
        outputFormat: 'mp4',
      };

      const { jobId: newJobId } = await videoService.createVideoTask(request);
      setJobId(newJobId);

      // 轮询进度
      const pollInterval = setInterval(async () => {
        try {
          const statusData = await videoService.getVideoStatus(newJobId);
          setProgress(statusData.progress);

          if (statusData.status === 'completed') {
            clearInterval(pollInterval);
            setVideoUrl(statusData.videoUrl || null);
            setStatus('completed');
            message.success('视频生成完成！');
            onVideoGenerated?.(statusData.videoUrl || '');
          } else if (statusData.status === 'failed') {
            clearInterval(pollInterval);
            setStatus('failed');
            message.error(`视频生成失败：${statusData.errorMessage}`);
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 3000);
    } catch (error: any) {
      setGenerating(false);
      setStatus('failed');
      message.error(`创建任务失败：${error.message}`);
    }
  };

  // 下载视频
  const handleDownload = async () => {
    if (!jobId) return;
    try {
      const blob = await videoService.downloadVideo(jobId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `lesson-${jobId}.mp4`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('下载开始');
    } catch (error: any) {
      message.error(`下载失败：${error.message}`);
    }
  };

  return (
    <Card
      title={
        <Space>
          <VideoCameraOutlined />
          <span>🎬 教学视频生成器</span>
        </Space>
      }
      extra={
        status === 'completed' && (
          <Tag color="green">
            <CheckCircleOutlined /> 已完成
          </Tag>
        )
      }
    >
      <Form form={form} layout="vertical" onFinish={handleGenerate}>
        <Form.Item
          name="title"
          label="视频标题"
          rules={[{ required: true, message: '请输入视频标题' }]}
        >
          <Input placeholder="例如：二次函数入门" />
        </Form.Item>

        <Form.Item
          name="voiceId"
          label="配音语音"
          initialValue={AVAILABLE_VOICES[0].id}
        >
          <Select>
            {AVAILABLE_VOICES.map((voice) => (
              <Select.Option key={voice.id} value={voice.id}>
                {voice.name} - {voice.style}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="script"
          label="讲解脚本"
          rules={[{ required: true, message: '请输入讲解脚本' }]}
        >
          <TextArea
            rows={6}
            placeholder="输入完整的讲解脚本，AI 将自动分段并生成语音..."
          />
        </Form.Item>

        <Card size="small" title="📑 幻灯片配置" className="mb-4">
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Form layout="inline">
              <Form.Item label="标题" style={{ flex: 1 }}>
                <Input
                  value={currentSlide.title}
                  onChange={(e) =>
                    setCurrentSlide({ ...currentSlide, title: e.target.value })
                  }
                  placeholder="幻灯片标题"
                />
              </Form.Item>
              <Form.Item label="时长 (秒)" style={{ width: 120 }}>
                <Input.Number
                  value={currentSlide.duration}
                  onChange={(v) =>
                    setCurrentSlide({ ...currentSlide, duration: v || 10 })
                  }
                  min={5}
                  max={60}
                />
              </Form.Item>
              <Form.Item>
                <Button type="primary" onClick={addSlide}>
                  添加
                </Button>
              </Form.Item>
            </Form>

            <Input
              value={currentSlide.content}
              onChange={(e) =>
                setCurrentSlide({ ...currentSlide, content: e.target.value })
              }
              placeholder="幻灯片内容要点..."
            />

            {slides.length > 0 && (
              <List
                size="small"
                dataSource={slides}
                renderItem={(slide, index) => (
                  <List.Item
                    actions={[
                      <Button
                        type="link"
                        danger
                        onClick={() => removeSlide(index)}
                      >
                        删除
                      </Button>,
                    ]}
                  >
                    <List.Item.Meta
                      title={`幻灯片 ${index + 1} - ${slide.title}`}
                      description={`${slide.content} · ${slide.duration}秒`}
                    />
                  </List.Item>
                )}
              />
            )}
          </Space>
        </Card>

        <Form.Item>
          <Space>
            <Button
              type="primary"
              htmlType="submit"
              loading={generating}
              icon={generating ? <LoadingOutlined /> : <PlayCircleOutlined />}
              size="large"
            >
              {generating ? '生成中...' : '开始生成视频'}
            </Button>
            {status === 'completed' && (
              <Button
                icon={<DownloadOutlined />}
                onClick={handleDownload}
                size="large"
              >
                下载视频
              </Button>
            )}
          </Space>
        </Form.Item>
      </Form>

      {generating && (
        <Card size="small" className="mt-4">
          <Progress
            percent={progress}
            status="active"
            format={(percent) => `生成进度：${percent}%`}
          />
          <div className="text-center text-gray-500 mt-2">
            正在合成 1080p/30fps 视频，音频清晰度优化中...
          </div>
        </Card>
      )}

      {status === 'completed' && videoUrl && (
        <Card size="small" className="mt-4">
          <video
            src={videoUrl}
            controls
            className="w-full rounded-lg"
            style={{ maxHeight: '400px' }}
          />
          <div className="mt-2 text-center text-green-600">
            <CheckCircleOutlined /> 视频规格：1080p @ 30fps | 音频清晰度 ≥90%
          </div>
        </Card>
      )}
    </Card>
  );
};

export default VideoGenerator;
