import React, { useEffect, useState } from 'react';
import {
  Card,
  List,
  Typography,
  Tag,
  Progress,
  Button,
  Spin,
} from 'antd';
import {
  PlayCircleOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  BookOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { courseApi } from '../services/api';
import type { Course as CourseType, Lesson } from '../types';

const { Title, Text, Paragraph } = Typography;

const Course: React.FC = () => {
  const { courseId } = useParams<{ courseId: string }>();
  const navigate = useNavigate();
  const [course, setCourse] = useState<CourseType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCourse = async () => {
      if (!courseId) return;
      setLoading(true);
      try {
        const data = await courseApi.getCourse(courseId);
        setCourse(data);
      } catch (error) {
        console.error('Failed to fetch course:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCourse();
  }, [courseId]);

  const handleLessonClick = (lesson: Lesson) => {
    navigate(`/course/${courseId}/lesson/${lesson.id}`);
  };

  const getLessonIcon = (type: Lesson['type']) => {
    switch (type) {
      case 'video':
        return <PlayCircleOutlined className="text-red-500" />;
      case 'text':
        return <FileTextOutlined className="text-blue-500" />;
      case 'exercise':
        return <CheckCircleOutlined className="text-green-500" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex justify-center">
        <Spin size="large" tip="加载课程中..." />
      </div>
    );
  }

  if (!course) {
    return (
      <div className="p-6">
        <Card>
          <Typography.Text type="secondary">课程不存在</Typography.Text>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* 课程头部 */}
      <Card className="mb-6">
        <div className="flex items-start gap-4">
          {course.thumbnail && (
            <img
              src={course.thumbnail}
              alt={course.title}
              className="w-32 h-24 object-cover rounded-lg"
            />
          )}
          <div className="flex-1">
            <Title level={2} className="!mb-2">
              <BookOutlined className="mr-2" />
              {course.title}
            </Title>
            <Paragraph type="secondary" className="!mb-4">
              {course.description}
            </Paragraph>
            <div className="flex items-center gap-4">
              <Progress
                percent={course.progress}
                format={() => `${course.progress}% 完成`}
                className="flex-1"
              />
              <Tag color="blue">{course.lessons.length} 课时</Tag>
            </div>
          </div>
        </div>
      </Card>

      {/* 课时列表 */}
      <Card title="📖 课时列表">
        <List
          dataSource={course.lessons}
          renderItem={(lesson, index) => (
            <List.Item
              className="cursor-pointer hover:bg-gray-50 p-4"
              onClick={() => handleLessonClick(lesson)}
            >
              <div className="flex items-center gap-4 flex-1">
                <div className="text-2xl">{getLessonIcon(lesson.type)}</div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Text strong>第 {index + 1} 课：{lesson.title}</Text>
                    {lesson.completed && (
                      <Tag color="success" icon={<CheckCircleOutlined />}>
                        已完成
                      </Tag>
                    )}
                  </div>
                  {lesson.duration && (
                    <Text type="secondary" className="text-sm">
                      ⏱️ {Math.floor(lesson.duration / 60)}:{(lesson.duration % 60)
                        .toString()
                        .padStart(2, '0')}
                    </Text>
                  )}
                </div>
                <Button type="link">
                  开始学习 →
                </Button>
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default Course;
