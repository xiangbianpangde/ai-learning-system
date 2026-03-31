/**
 * 费曼测试 UI 组件
 * 基于费曼学习法：通过教授他人来检验理解程度
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Input,
  Rate,
  Progress,
  Space,
  Tag,
  Collapse,
  message,
  Avatar,
  List,
  Timeline,
} from 'antd';
import {
  UserOutlined,
  BookOutlined,
  CheckCircleOutlined,
  StarOutlined,
  VideoCameraOutlined,
  SendOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '../../store';

const { TextArea } = Input;
const { Panel } = Collapse;

export interface FeynmanSession {
  id: string;
  topic: string;
  concept: string;
  status: 'preparing' | 'teaching' | 'reviewing' | 'completed';
  startTime?: number;
  endTime?: number;
  selfRating?: number;
  feedback?: string;
  recordingUrl?: string;
}

export interface FeynmanTestProps {
  topic: string;
  concept: string;
  onComplete?: (session: FeynmanSession) => void;
}

const FeynmanTest: React.FC<FeynmanTestProps> = ({
  topic,
  concept,
  onComplete,
}) => {
  const { user } = useAuthStore();
  const [session, setSession] = useState<FeynmanSession>({
    id: `feynman-${Date.now()}`,
    topic,
    concept,
    status: 'preparing',
  });
  const [explanation, setExplanation] = useState('');
  const [selfRating, setSelfRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [timeElapsed, setTimeElapsed] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // 计时器
  useEffect(() => {
    if (session.status === 'teaching') {
      timerRef.current = setInterval(() => {
        setTimeElapsed((prev) => prev + 1);
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
  }, [session.status]);

  // 格式化时间
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 开始教学
  const startTeaching = () => {
    setSession({ ...session, status: 'teaching', startTime: Date.now() });
    message.info('🎤 开始你的讲解！想象你在教一个完全不懂的人...');
  };

  // 提交讲解
  const submitExplanation = () => {
    if (!explanation.trim()) {
      message.warning('请先写下你的讲解内容');
      return;
    }

    setSession({
      ...session,
      status: 'reviewing',
      explanation,
    });
    message.success('讲解已提交，现在进行自我评估...');
  };

  // 完成测试
  const completeTest = () => {
    const completedSession: FeynmanSession = {
      ...session,
      status: 'completed',
      selfRating,
      feedback,
      endTime: Date.now(),
    };

    setSession(completedSession);
    onComplete?.(completedSession);
    message.success('🎉 费曼测试完成！');
  };

  // 录音功能 (模拟)
  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      message.success('录音已保存');
    } else {
      setIsRecording(true);
      message.info('🔴 录音中...');
    }
  };

  // 费曼学习法四步提示
  const feynmanSteps = [
    { title: 'Step 1', desc: '选择一个概念', icon: '📚' },
    { title: 'Step 2', desc: '教授给他人', icon: '🎤' },
    { title: 'Step 3', desc: '发现知识盲点', icon: '🔍' },
    { title: 'Step 4', desc: '简化并重新组织', icon: '✨' },
  ];

  if (session.status === 'completed') {
    return (
      <Card
        title="✅ 费曼测试完成"
        extra={<Tag color="green">已完成</Tag>}
        className="mb-4"
      >
        <div className="text-center">
          <Avatar size={80} icon={<BookOutlined />} className="mb-4 bg-blue-500" />
          
          <h2 className="text-2xl font-bold mb-2">{session.concept}</h2>
          <p className="text-gray-500 mb-4">{session.topic}</p>

          <div className="flex justify-center gap-8 mb-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {formatTime(timeElapsed)}
              </div>
              <div className="text-gray-500">讲解时长</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-yellow-500">
                {selfRating}
                <StarOutlined />
              </div>
              <div className="text-gray-500">自我评分</div>
            </div>
          </div>

          <Card size="small" className="text-left mb-4">
            <h4 className="font-semibold mb-2">📝 你的讲解</h4>
            <p className="text-gray-700 whitespace-pre-wrap">{explanation}</p>
          </Card>

          {feedback && (
            <Card size="small" className="text-left">
              <h4 className="font-semibold mb-2">💭 反思与改进</h4>
              <p className="text-gray-700">{feedback}</p>
            </Card>
          )}

          <Button
            type="primary"
            size="large"
            className="mt-6"
            onClick={() => onComplete?.(session)}
          >
            继续学习
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <BookOutlined />
          <span>🎓 费曼测试</span>
        </Space>
      }
      extra={
        <Tag color={session.status === 'teaching' ? 'blue' : 'default'}>
          {session.status === 'preparing' && '准备中'}
          {session.status === 'teaching' && '讲解中'}
          {session.status === 'reviewing' && '评估中'}
        </Tag>
      }
      className="mb-4"
    >
      {/* 进度指示 */}
      <Timeline
        items={[
          {
            title: '准备阶段',
            color: session.status === 'preparing' ? 'blue' : 'green',
            children: '理解概念，组织思路',
          },
          {
            title: '讲解阶段',
            color: session.status === 'teaching' ? 'blue' : session.status !== 'preparing' ? 'green' : 'gray',
            children: '用自己的话解释概念',
          },
          {
            title: '反思阶段',
            color: session.status === 'reviewing' ? 'blue' : session.status === 'completed' ? 'green' : 'gray',
            children: '发现盲点，自我评估',
          },
        ]}
        className="mb-6"
      />

      {/* 准备阶段 */}
      {session.status === 'preparing' && (
        <div>
          <Card size="small" className="mb-4 bg-blue-50">
            <h3 className="font-semibold mb-2">
              📌 测试主题：{concept}
            </h3>
            <p className="text-gray-600">
              请用简单易懂的语言解释这个概念，就像在教一个完全不懂的人。
              避免使用专业术语，多用类比和例子。
            </p>
          </Card>

          <Collapse>
            <Panel header="💡 费曼学习法技巧" key="tips">
              <List
                size="small"
                dataSource={[
                  '用简单的语言，避免 jargon',
                  '多举例子和类比',
                  '想象听众是初学者',
                  '录音回听，发现不清楚的地方',
                ]}
                renderItem={(item) => <List.Item>• {item}</List.Item>}
              />
            </Panel>
          </Collapse>

          <Button
            type="primary"
            size="large"
            className="mt-6"
            onClick={startTeaching}
            icon={<PlayCircleOutlined />}
          >
            开始讲解
          </Button>
        </div>
      )}

      {/* 讲解阶段 */}
      {session.status === 'teaching' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <Space>
              <Tag color="blue">⏱ {formatTime(timeElapsed)}</Tag>
              {isRecording && <Tag color="red">🔴 录音中</Tag>}
            </Space>
            <Button
              onClick={toggleRecording}
              icon={<VideoCameraOutlined />}
              danger={isRecording}
            >
              {isRecording ? '停止录音' : '开始录音'}
            </Button>
          </div>

          <TextArea
            value={explanation}
            onChange={(e) => setExplanation(e.target.value)}
            placeholder="在这里写下你的讲解...

提示：
1. 这个概念是什么？
2. 它为什么重要？
3. 它是如何工作的？
4. 能举个例子吗？"
            rows={12}
            className="mb-4"
          />

          <Space>
            <Button
              type="primary"
              size="large"
              onClick={submitExplanation}
              icon={<SendOutlined />}
            >
              提交讲解
            </Button>
            <Button onClick={() => setSession({ ...session, status: 'preparing' })}>
              重新准备
            </Button>
          </Space>
        </div>
      )}

      {/* 评估阶段 */}
      {session.status === 'reviewing' && (
        <div>
          <Card size="small" className="mb-4">
            <h4 className="font-semibold mb-2">📝 你的讲解</h4>
            <p className="text-gray-700 whitespace-pre-wrap">{explanation}</p>
          </Card>

          <Card size="small" className="mb-4">
            <h4 className="font-semibold mb-2">⭐ 自我评估</h4>
            <p className="text-gray-600 mb-2">
              你的讲解是否清晰易懂？一个完全不懂的人能理解吗？
            </p>
            <Rate
              value={selfRating}
              onChange={setSelfRating}
              character={<StarOutlined />}
              className="text-2xl"
            />
            <div className="mt-2 text-gray-500">
              {selfRating === 5 && '🌟 非常清晰！'}
              {selfRating === 4 && '👍 很好，有小改进空间'}
              {selfRating === 3 && '👌 基本清楚'}
              {selfRating === 2 && '💭 需要更多解释'}
              {selfRating === 1 && '📚 需要重新学习'}
              {selfRating === 0 && '请评分'}
            </div>
          </Card>

          <Card size="small" className="mb-4">
            <h4 className="font-semibold mb-2">💭 反思与改进</h4>
            <TextArea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="哪些地方讲得不够清楚？需要补充什么？"
              rows={3}
            />
          </Card>

          <Button
            type="primary"
            size="large"
            onClick={completeTest}
            disabled={selfRating === 0}
            icon={<CheckCircleOutlined />}
          >
            完成测试
          </Button>
        </div>
      )}
    </Card>
  );
};

export default FeynmanTest;
