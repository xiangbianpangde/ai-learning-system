/**
 * 费曼测试组件 v2
 * 费曼学习法四步流程：
 * 1. 选择概念
 * 2. 教学 (录音 + 计时)
 * 3. 回顾与反思
 * 4. 简化与类比
 * 
 * 新增功能:
 * - 录音功能完善
 * - 计时器优化
 * - 反思提示
 * - 自我评估
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Input,
  Progress,
  Rate,
  Timeline,
  message,
  Collapse,
  Result,
  Tag,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  AudioOutlined,
  CheckCircleOutlined,
  BookOutlined,
  LightbulbOutlined,
  EditOutlined,
  RedoOutlined,
  TrophyOutlined,
} from '@ant-design/icons';

const { TextArea } = Input;
const { Panel } = Collapse;

export interface FeynmanSession {
  id: string;
  topic: string;
  concept: string;
  startTime: number;
  endTime?: number;
  teachingDuration: number; // seconds
  recording?: Blob;
  reflection: string;
  simplifications: string[];
  analogies: string[];
  selfRating: number; // 1-5
  gaps: string[];
  nextSteps: string[];
}

interface FeynmanTestProps {
  topic: string;
  concept: string;
  onComplete?: (session: FeynmanSession) => void;
}

type FeynmanStep = 'select' | 'teach' | 'reflect' | 'simplify' | 'complete';

const FeynmanTest: React.FC<FeynmanTestProps> = ({
  topic,
  concept,
  onComplete,
}) => {
  const [currentStep, setCurrentStep] = useState<FeynmanStep>('select');
  const [teachingTime, setTeachingTime] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingBlob, setRecordingBlob] = useState<Blob | null>(null);
  const [reflection, setReflection] = useState('');
  const [simplifications, setSimplifications] = useState<string[]>([]);
  const [analogies, setAnalogies] = useState<string[]>([]);
  const [selfRating, setSelfRating] = useState(0);
  const [gaps, setGaps] = useState<string[]>([]);
  const [newGap, setNewGap] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const sessionRef = useRef<FeynmanSession | null>(null);

  // 初始化会话
  useEffect(() => {
    sessionRef.current = {
      id: `feynman-${Date.now()}`,
      topic,
      concept,
      startTime: Date.now(),
      teachingDuration: 0,
      reflection: '',
      simplifications: [],
      analogies: [],
      selfRating: 0,
      gaps: [],
      nextSteps: [],
    };
  }, [topic, concept]);

  // 计时器
  useEffect(() => {
    if (isRecording && currentStep === 'teach') {
      timerRef.current = setInterval(() => {
        setTeachingTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording, currentStep]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 开始录音
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setRecordingBlob(blob);
        if (sessionRef.current) {
          sessionRef.current.recording = blob;
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      message.info('🎤 开始教学，请像教别人一样讲解这个概念');
    } catch (error) {
      message.error('无法访问麦克风，请检查权限设置');
    }
  };

  // 停止录音
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      setIsRecording(false);
      
      if (sessionRef.current) {
        sessionRef.current.teachingDuration = teachingTime;
      }
      
      message.success('🎤 教学完成，请回顾并反思');
      setCurrentStep('reflect');
    }
  };

  // 添加知识盲点
  const addGap = () => {
    if (newGap.trim()) {
      setGaps([...gaps, newGap.trim()]);
      setNewGap('');
      message.success('已添加知识盲点');
    }
  };

  // 添加简化版本
  const addSimplification = () => {
    if (sessionRef.current) {
      sessionRef.current.simplifications = simplifications;
      sessionRef.current.analogies = analogies;
      sessionRef.current.reflection = reflection;
      sessionRef.current.selfRating = selfRating;
      sessionRef.current.gaps = gaps;
      sessionRef.current.endTime = Date.now();
    }
    
    onComplete?.(sessionRef.current!);
    setCurrentStep('complete');
  };

  // 步骤进度
  const steps = [
    { key: 'select', title: '选择概念', icon: <BookOutlined /> },
    { key: 'teach', title: '教学', icon: <AudioOutlined /> },
    { key: 'reflect', title: '反思', icon: <EditOutlined /> },
    { key: 'simplify', title: '简化', icon: <LightbulbOutlined /> },
    { key: 'complete', title: '完成', icon: <TrophyOutlined /> },
  ];

  const currentStepIndex = steps.findIndex((s) => s.key === currentStep);

  // 渲染各步骤
  const renderStep = () => {
    switch (currentStep) {
      case 'select':
        return (
          <div className="text-center py-8">
            <h2 className="text-2xl font-bold mb-4">📚 费曼学习法</h2>
            <p className="text-gray-600 mb-6">
              通过"教"来学——如果你不能简单地解释它，你就没有真正理解它
            </p>
            
            <Card className="mb-4">
              <h3 className="text-lg font-semibold mb-2">当前概念</h3>
              <div className="text-xl text-blue-600">{concept}</div>
              <div className="text-gray-500 mt-1">{topic}</div>
            </Card>

            <div className="mb-6">
              <h4 className="font-medium mb-2">费曼技巧四步流程:</h4>
              <Timeline
                items={[
                  {
                    children: '🎯 选择一个概念',
                    color: 'blue',
                  },
                  {
                    children: '🎤 教学：假装你在教别人',
                    color: 'blue',
                  },
                  {
                    children: '🤔 反思：找出知识盲点',
                    color: 'blue',
                  },
                  {
                    children: '💡 简化：用类比和简单语言重新解释',
                    color: 'blue',
                  },
                ]}
              />
            </div>

            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={() => setCurrentStep('teach')}
            >
              开始学习
            </Button>
          </div>
        );

      case 'teach':
        return (
          <div className="text-center py-8">
            <h2 className="text-2xl font-bold mb-4">🎤 教学阶段</h2>
            <p className="text-gray-600 mb-6">
              想象你在给一个完全不懂的人讲解这个概念
            </p>

            <Card className="mb-6">
              <div className="text-6xl font-mono mb-4">
                {formatTime(teachingTime)}
              </div>
              <div className="flex justify-center gap-4">
                {!isRecording ? (
                  <Button
                    type="primary"
                    size="large"
                    icon={<AudioOutlined />}
                    onClick={startRecording}
                  >
                    开始录音
                  </Button>
                ) : (
                  <Button
                    danger
                    size="large"
                    icon={<StopOutlined />}
                    onClick={stopRecording}
                  >
                    结束教学
                  </Button>
                )}
              </div>
              {recordingBlob && (
                <div className="mt-4">
                  <audio src={URL.createObjectURL(recordingBlob)} controls />
                </div>
              )}
            </Card>

            <Collapse>
              <Panel header="💡 教学提示" key="tips">
                <ul className="space-y-2">
                  <li>✅ 使用简单的语言，避免专业术语</li>
                  <li>✅ 用自己的话解释，不要背诵</li>
                  <li>✅ 举例说明抽象概念</li>
                  <li>✅ 如果卡住了，标记下来稍后回顾</li>
                </ul>
              </Panel>
            </Collapse>

            {teachingTime > 0 && !isRecording && (
              <Button
                type="primary"
                className="mt-4"
                onClick={() => setCurrentStep('reflect')}
              >
                进入反思 →
              </Button>
            )}
          </div>
        );

      case 'reflect':
        return (
          <div className="py-8">
            <h2 className="text-2xl font-bold mb-4">🤔 反思阶段</h2>
            <p className="text-gray-600 mb-6">
              回顾刚才的教学，找出你不清楚或卡住的地方
            </p>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">教学时长</h3>
              <div className="text-2xl text-blue-600">{formatTime(teachingTime)}</div>
            </Card>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">
                自我评估 <span className="text-sm text-gray-500">(1-5 星)</span>
              </h3>
              <Rate
                value={selfRating}
                onChange={setSelfRating}
                className="text-lg"
              />
              <div className="mt-2 text-sm text-gray-500">
                {selfRating === 5 && '🌟 非常清晰！'}
                {selfRating === 4 && '👍 基本理解'}
                {selfRating === 3 && '🤔 还需要加强'}
                {selfRating === 2 && '😅 有些困惑'}
                {selfRating === 1 && '😓 需要重新学习'}
              </div>
            </Card>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">知识盲点</h3>
              <p className="text-sm text-gray-500 mb-2">
                哪些地方你解释不清楚？哪些概念你还不理解？
              </p>
              <Space.Compact className="w-full mb-2">
                <Input
                  placeholder="例如：我不太清楚 XX 是如何推导的..."
                  value={newGap}
                  onChange={(e) => setNewGap(e.target.value)}
                  onPressEnter={addGap}
                />
                <Button type="primary" onClick={addGap}>
                  添加
                </Button>
              </Space.Compact>
              
              {gaps.length > 0 && (
                <div className="mt-2">
                  {gaps.map((gap, index) => (
                    <Tag
                      key={index}
                      closable
                      onClose={() => setGaps(gaps.filter((_, i) => i !== index))}
                      className="mb-1"
                    >
                      {gap}
                    </Tag>
                  ))}
                </div>
              )}
            </Card>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">反思笔记</h3>
              <TextArea
                rows={4}
                placeholder="写下你的反思：哪些地方讲得好？哪些地方需要改进？..."
                value={reflection}
                onChange={(e) => setReflection(e.target.value)}
              />
            </Card>

            <Button
              type="primary"
              onClick={() => setCurrentStep('simplify')}
              disabled={gaps.length === 0 && selfRating === 0}
            >
              进入简化 →
            </Button>
          </div>
        );

      case 'simplify':
        return (
          <div className="py-8">
            <h2 className="text-2xl font-bold mb-4">💡 简化阶段</h2>
            <p className="text-gray-600 mb-6">
              用更简单的语言和类比重新解释这个概念
            </p>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">简化版本</h3>
              <p className="text-sm text-gray-500 mb-2">
                尝试用小学生能听懂的话来解释
              </p>
              <TextArea
                rows={4}
                placeholder="这个概念就像... 它的作用是..."
                value={simplifications.join('\n')}
                onChange={(e) => setSimplifications([e.target.value])}
              />
            </Card>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">类比解释</h3>
              <p className="text-sm text-gray-500 mb-2">
                找一些生活中的例子来类比
              </p>
              <TextArea
                rows={3}
                placeholder="这就像... 类似于..."
                value={analogies.join('\n')}
                onChange={(e) => setAnalogies([e.target.value])}
              />
            </Card>

            <Card className="mb-4">
              <h3 className="font-semibold mb-2">下一步学习计划</h3>
              <Collapse>
                <Panel header="📚 建议学习资源" key="resources">
                  <ul className="space-y-1">
                    <li>• 复习教材相关章节</li>
                    <li>• 观看教学视频</li>
                    <li>• 做相关练习题</li>
                    <li>• 向老师或同学请教</li>
                  </ul>
                </Panel>
              </Collapse>
            </Card>

            <Button
              type="primary"
              size="large"
              onClick={addSimplification}
              icon={<CheckCircleOutlined />}
            >
              完成学习
            </Button>
          </div>
        );

      case 'complete':
        return (
          <Result
            icon={<TrophyOutlined style={{ color: '#faad14' }} />}
            title="🎉 费曼学习完成！"
            subTitle={
              <div className="text-center">
                <p className="mb-2">
                  教学时长：<strong>{formatTime(teachingTime)}</strong>
                </p>
                <p className="mb-2">
                  自我评分：<Rate disabled value={selfRating} />
                </p>
                <p>
                  知识盲点：<strong>{gaps.length}</strong> 个
                </p>
              </div>
            }
            extra={
              <Space>
                <Button onClick={() => {
                  setTeachingTime(0);
                  setRecordingBlob(null);
                  setReflection('');
                  setSimplifications([]);
                  setAnalogies([]);
                  setSelfRating(0);
                  setGaps([]);
                  setCurrentStep('select');
                }} icon={<RedoOutlined />}>
                  再来一次
                </Button>
                <Button type="primary">查看学习报告</Button>
              </Space>
            }
          />
        );

      default:
        return null;
    }
  };

  return (
    <Card
      title={`🎓 费曼学习法：${concept}`}
      className="max-w-3xl mx-auto"
    >
      {/* 步骤进度条 */}
      {currentStep !== 'complete' && (
        <Progress
          percent={((currentStepIndex + 1) / steps.length) * 100}
          showInfo={false}
          className="mb-6"
        />
      )}

      {renderStep()}
    </Card>
  );
};

export default FeynmanTest;
