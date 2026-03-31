import React, { useEffect, useState } from 'react';
import {
  Card,
  Typography,
  Radio,
  Button,
  Space,
  Spin,
  Alert,
  Result,
  Input,
} from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { exerciseApi } from '../services/api';
import type { Exercise as ExerciseType, ExerciseResult } from '../types';

const { Title, Text } = Typography;
const { TextArea } = Input;

const Exercise: React.FC = () => {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const navigate = useNavigate();
  const [exercise, setExercise] = useState<ExerciseType | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [textAnswer, setTextAnswer] = useState<string>('');
  const [result, setResult] = useState<ExerciseResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchExercise = async () => {
      if (!lessonId) return;
      setLoading(true);
      try {
        // 获取练习列表中的第一个练习（简化处理）
        const history = await exerciseApi.getExerciseHistory(lessonId);
        if (history.length > 0) {
          // 如果有历史记录，可以显示之前的练习
          // 这里简化处理，直接获取练习
        }
        // 实际应该通过 API 获取当前课时的练习
        // 这里使用模拟数据
        setExercise({
          id: lessonId,
          lessonId,
          type: 'multiple-choice',
          question: '以下哪个是 React 的核心概念？',
          options: ['组件', '路由', '状态管理', '以上都是'],
          correctAnswer: '以上都是',
          explanation: 'React 的核心概念包括组件、状态、Props 等，路由和状态管理是生态系统的组成部分。',
        });
      } catch (error) {
        console.error('Failed to fetch exercise:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchExercise();
  }, [lessonId]);

  const handleSubmit = async () => {
    const answer = exercise?.type === 'multiple-choice' ? selectedAnswer : textAnswer;
    if (!answer || !exercise) return;

    setSubmitting(true);
    try {
      const exerciseResult = await exerciseApi.submitExercise(exercise.id, answer);
      setResult(exerciseResult);
    } catch (error) {
      console.error('Failed to submit exercise:', error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center">
        <Spin size="large" tip="加载练习..." />
      </div>
    );
  }

  if (!exercise) {
    return (
      <div className="p-6">
        <Card>
          <Alert message="练习不存在" type="error" />
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* 返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(`/course/${courseId}/lesson/${lessonId}`)}
        className="mb-4"
      >
        返回课时
      </Button>

      {/* 练习题目 */}
      <Card title="💡 练习题" className="mb-6">
        <Title level={4}>{exercise.question}</Title>

        {exercise.type === 'multiple-choice' && exercise.options && (
          <Radio.Group
            value={selectedAnswer}
            onChange={(e) => setSelectedAnswer(e.target.value)}
            className="mt-4 space-y-3"
          >
            {exercise.options.map((option, index) => (
              <div key={index} className="block">
                <Radio value={option} className="text-lg p-3 border rounded hover:bg-gray-50 w-full">
                  {option}
                </Radio>
              </div>
            ))}
          </Radio.Group>
        )}

        {exercise.type === 'fill-blank' && (
          <TextArea
            value={textAnswer}
            onChange={(e) => setTextAnswer(e.target.value)}
            placeholder="请输入答案..."
            autoSize={{ minRows: 3, maxRows: 6 }}
            className="mt-4"
          />
        )}

        {!result && (
          <div className="mt-6 flex justify-end">
            <Button
              type="primary"
              size="large"
              onClick={handleSubmit}
              loading={submitting}
              disabled={
                exercise.type === 'multiple-choice' ? !selectedAnswer : !textAnswer
              }
            >
              提交答案
            </Button>
          </div>
        )}
      </Card>

      {/* 结果反馈 */}
      {result && (
        <Card>
          <Result
            icon={
              result.isCorrect ? (
                <CheckCircleOutlined className="text-green-500 text-6xl" />
              ) : (
                <CloseCircleOutlined className="text-red-500 text-6xl" />
              )
            }
            title={result.isCorrect ? '🎉 回答正确！' : '❌ 回答错误'}
            subTitle={result.feedback}
            extra={
              <Space>
                {!result.isCorrect && result.correctAnswer && (
                  <Text type="secondary">
                    正确答案：{result.correctAnswer}
                  </Text>
                )}
                <Button type="primary" onClick={() => navigate(`/course/${courseId}`)}>
                  继续学习
                </Button>
                <Button onClick={() => {
                  setResult(null);
                  setSelectedAnswer('');
                  setTextAnswer('');
                }}>
                  再试一次
                </Button>
              </Space>
            }
          />
          {result && (
            <Alert
              message="📚 解析"
              description={exercise.explanation}
              type="info"
              showIcon
              className="mt-4"
            />
          )}
        </Card>
      )}
    </div>
  );
};

export default Exercise;
