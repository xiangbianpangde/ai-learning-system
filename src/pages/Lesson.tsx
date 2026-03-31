import React, { useEffect, useState } from 'react';
import { Card, Typography, Button, Space, Spin, Alert, Divider } from 'antd';
import { ArrowLeftOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { courseApi, learningApi } from '../services/api';
import { useLearningStore } from '../store';
import type { Lesson as LessonType } from '../types';

const { Paragraph, Text } = Typography;

const Lesson: React.FC = () => {
  const { courseId, lessonId } = useParams<{ courseId: string; lessonId: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<LessonType | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const { updateLessonProgress } = useLearningStore();

  useEffect(() => {
    const fetchLesson = async () => {
      if (!courseId || !lessonId) return;
      setLoading(true);
      try {
        const data = await courseApi.getLesson(courseId, lessonId);
        setLesson(data);
      } catch (error) {
        console.error('Failed to fetch lesson:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchLesson();
  }, [courseId, lessonId]);

  const handleComplete = async () => {
    if (!courseId || !lessonId) return;
    setCompleting(true);
    try {
      await learningApi.updateProgress(courseId, lessonId);
      updateLessonProgress(courseId, lessonId);
    } catch (error) {
      console.error('Failed to update progress:', error);
    } finally {
      setCompleting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center">
        <Spin size="large" tip="加载课时内容..." />
      </div>
    );
  }

  if (!lesson) {
    return (
      <div className="p-6">
        <Card>
          <Alert message="课时不存在" type="error" />
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* 返回按钮 */}
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(`/course/${courseId}`)}
        className="mb-4"
      >
        返回课程
      </Button>

      {/* 课时内容 */}
      <Card title={lesson.title} className="mb-6">
        {lesson.type === 'video' && lesson.videoUrl && (
          <div className="mb-6">
            <div className="aspect-video bg-black rounded-lg flex items-center justify-center">
              <video
                src={lesson.videoUrl}
                controls
                className="w-full h-full rounded-lg"
              >
                您的浏览器不支持视频播放
              </video>
            </div>
            {lesson.duration && (
              <Text type="secondary" className="block mt-2">
                ⏱️ 时长：{Math.floor(lesson.duration / 60)}:{(lesson.duration % 60)
                  .toString()
                  .padStart(2, '0')}
              </Text>
            )}
          </div>
        )}

        {lesson.type === 'text' && (
          <div className="prose max-w-none">
            <Paragraph className="text-lg leading-relaxed">
              {lesson.content}
            </Paragraph>
          </div>
        )}

        {lesson.type === 'exercise' && (
          <Alert
            message="💡 练习环节"
            description="完成下面的练习来巩固所学知识"
            type="info"
            showIcon
            className="mb-4"
          />
        )}

        <Divider />

        {/* 完成按钮 */}
        <div className="flex justify-between items-center">
          <Text type="secondary">
            {lesson.completed ? (
              <span className="text-green-600">
                <CheckCircleOutlined /> 已完成
              </span>
            ) : (
              '完成学习后点击完成按钮'
            )}
          </Text>
          <Space>
            {lesson.type === 'exercise' && (
              <Button
                type="primary"
                onClick={() => navigate(`/course/${courseId}/lesson/${lessonId}/exercise`)}
              >
                开始练习
              </Button>
            )}
            <Button
              type="primary"
              onClick={handleComplete}
              loading={completing}
              disabled={lesson.completed}
            >
              {lesson.completed ? '已完成' : '标记为完成'}
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default Lesson;
