/**
 * 学习仪表盘组件 v2
 * 综合展示学习进度、成就、推荐
 * 
 * 功能:
 * - 学习进度追踪
 * - 成就系统
 * - 智能推荐
 * - 响应式设计
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Statistic,
  Timeline,
  Badge,
  Button,
  Space,
  Tag,
  Avatar,
  List,
  Tooltip,
} from 'antd';
import {
  TrophyOutlined,
  BookOutlined,
  ClockCircleOutlined,
  FireOutlined,
  StarOutlined,
  ThunderboltOutlined,
  RiseOutlined,
  PlayCircleOutlined,
} from '@ant-design/icons';

// 学习进度数据
interface LearningProgress {
  totalLessons: number;
  completedLessons: number;
  totalVideos: number;
  watchedVideos: number;
  totalQuizzes: number;
  passedQuizzes: number;
  studyStreak: number; // 连续学习天数
  totalStudyTime: number; // 分钟
}

// 成就数据
interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress: number; // 0-100
  requirement: number;
}

// 推荐数据
interface Recommendation {
  id: string;
  type: 'lesson' | 'video' | 'quiz' | 'practice';
  title: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  estimatedTime: number; // 分钟
  priority: number; // 1-5
}

interface DashboardProps {
  userId?: string;
  userName?: string;
}

const Dashboard: React.FC<DashboardProps> = ({
  userId = 'demo-user',
  userName = '学习者',
}) => {
  const [progress, setProgress] = useState<LearningProgress>({
    totalLessons: 50,
    completedLessons: 32,
    totalVideos: 30,
    watchedVideos: 18,
    totalQuizzes: 40,
    passedQuizzes: 35,
    studyStreak: 7,
    totalStudyTime: 1250,
  });

  const [achievements, setAchievements] = useState<Achievement[]>([
    {
      id: 'first-lesson',
      title: '第一步',
      description: '完成第一节课',
      icon: '🎯',
      unlocked: true,
      progress: 100,
      requirement: 1,
    },
    {
      id: 'week-streak',
      title: '持之以恒',
      description: '连续学习 7 天',
      icon: '🔥',
      unlocked: true,
      progress: 100,
      requirement: 7,
    },
    {
      id: 'quiz-master',
      title: '测验达人',
      description: '通过 30 次测验',
      icon: '⭐',
      unlocked: true,
      progress: 100,
      requirement: 30,
    },
    {
      id: 'video-watcher',
      title: '视频达人',
      description: '观看 20 个视频',
      icon: '🎬',
      unlocked: false,
      progress: 90,
      requirement: 20,
    },
    {
      id: 'lesson-complete',
      title: '课程完成者',
      description: '完成所有课程',
      icon: '🏆',
      unlocked: false,
      progress: 64,
      requirement: 50,
    },
    {
      id: 'month-streak',
      title: '月度挑战',
      description: '连续学习 30 天',
      icon: '💪',
      unlocked: false,
      progress: 23,
      requirement: 30,
    },
  ]);

  const [recommendations, setRecommendations] = useState<Recommendation[]>([
    {
      id: 'rec-1',
      type: 'lesson',
      title: '二次函数的应用',
      description: '学习如何将二次函数应用到实际问题中',
      difficulty: 'medium',
      estimatedTime: 25,
      priority: 5,
    },
    {
      id: 'rec-2',
      type: 'video',
      title: '抛物线的几何性质',
      description: '通过视频深入了解抛物线',
      difficulty: 'medium',
      estimatedTime: 15,
      priority: 4,
    },
    {
      id: 'rec-3',
      type: 'quiz',
      title: '二次方程综合测验',
      description: '检验你的学习成果',
      difficulty: 'hard',
      estimatedTime: 20,
      priority: 4,
    },
    {
      id: 'rec-4',
      type: 'practice',
      title: '应用题专项练习',
      description: '强化实际应用能力',
      difficulty: 'medium',
      estimatedTime: 30,
      priority: 3,
    },
  ]);

  // 计算完成率
  const lessonProgress = (progress.completedLessons / progress.totalLessons) * 100;
  const videoProgress = (progress.watchedVideos / progress.totalVideos) * 100;
  const quizProgress = (progress.passedQuizzes / progress.totalQuizzes) * 100;

  // 难度标签颜色
  const difficultyColors = {
    easy: 'green',
    medium: 'blue',
    hard: 'red',
  };

  // 类型标签
  const typeLabels = {
    lesson: '📖 课程',
    video: '🎬 视频',
    quiz: '📝 测验',
    practice: '✏️ 练习',
  };

  return (
    <div className="p-6">
      {/* 顶部欢迎区 */}
      <Card className="mb-6">
        <Row align="middle" gutter={16}>
          <Col>
            <Avatar size={64} icon="👤" style={{ backgroundColor: '#1890ff' }} />
          </Col>
          <Col flex="auto">
            <h1 className="text-2xl font-bold mb-1">欢迎回来，{userName}!</h1>
            <p className="text-gray-600">
              你已经连续学习 <strong>{progress.studyStreak} 天</strong>，继续保持！
            </p>
          </Col>
          <Col>
            <Space size="large">
              <Statistic
                title="总学习时长"
                value={Math.floor(progress.totalStudyTime / 60)}
                suffix="小时"
                prefix={<ClockCircleOutlined />}
              />
              <Statistic
                title="连续学习"
                value={progress.studyStreak}
                suffix="天"
                prefix={<FireOutlined style={{ color: '#fa541c' }} />}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 学习进度 */}
      <Row gutter={16} className="mb-6">
        <Col xs={24} md={8}>
          <Card title="📚 课程进度">
            <Progress
              type="dashboard"
              percent={Math.round(lessonProgress)}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
              format={(percent) => `${percent}%`}
            />
            <div className="text-center mt-4 text-gray-600">
              {progress.completedLessons} / {progress.totalLessons} 节课
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title="🎬 视频进度">
            <Progress
              type="dashboard"
              percent={Math.round(videoProgress)}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div className="text-center mt-4 text-gray-600">
              {progress.watchedVideos} / {progress.totalVideos} 个视频
            </div>
          </Card>
        </Col>

        <Col xs={24} md={8}>
          <Card title="📝 测验进度">
            <Progress
              type="dashboard"
              percent={Math.round(quizProgress)}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <div className="text-center mt-4 text-gray-600">
              {progress.passedQuizzes} / {progress.totalQuizzes} 次测验
            </div>
          </Card>
        </Col>
      </Row>

      {/* 成就系统 */}
      <Card title="🏆 成就系统" className="mb-6">
        <Row gutter={16}>
          {achievements.map((achievement) => (
            <Col xs={12} sm={8} md={4} key={achievement.id}>
              <div
                className={`text-center p-4 rounded-lg border-2 ${
                  achievement.unlocked
                    ? 'border-yellow-400 bg-yellow-50'
                    : 'border-gray-200 bg-gray-50 opacity-60'
                }`}
              >
                <div className="text-4xl mb-2">{achievement.icon}</div>
                <div className="font-semibold text-sm mb-1">
                  {achievement.title}
                </div>
                <div className="text-xs text-gray-600 mb-2">
                  {achievement.description}
                </div>
                <Progress
                  percent={achievement.progress}
                  showInfo={false}
                  size="small"
                  strokeColor={achievement.unlocked ? '#faad14' : '#d9d9d9'}
                />
                <div className="text-xs text-gray-500 mt-1">
                  {Math.round(achievement.progress)} / {achievement.requirement}
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* 智能推荐 */}
      <Row gutter={16}>
        <Col xs={24} lg={16}>
          <Card
            title="💡 为你推荐"
            extra={
              <Button type="link">
                查看全部 <RiseOutlined />
              </Button>
            }
          >
            <List
              dataSource={recommendations}
              renderItem={(item) => (
                <List.Item
                  actions={[
                    <Button
                      type="primary"
                      size="small"
                      icon={<PlayCircleOutlined />}
                    >
                      开始
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        style={{ backgroundColor: '#1890ff' }}
                        icon={<BookOutlined />}
                      />
                    }
                    title={
                      <Space>
                        <span>{item.title}</span>
                        <Tag color={difficultyColors[item.difficulty]}>
                          {item.difficulty === 'easy' && '简单'}
                          {item.difficulty === 'medium' && '中等'}
                          {item.difficulty === 'hard' && '困难'}
                        </Tag>
                        <Tag>{typeLabels[item.type]}</Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <p className="mb-1">{item.description}</p>
                        <Space size="small">
                          <span className="text-gray-500">
                            <ClockCircleOutlined /> 预计 {item.estimatedTime} 分钟
                          </span>
                          <span>
                            优先级：
                            {[...Array(5)].map((_, i) => (
                              <StarOutlined
                                key={i}
                                style={{
                                  color: i < item.priority ? '#faad14' : '#d9d9d9',
                                }}
                              />
                            ))}
                          </span>
                        </Space>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="📊 学习统计">
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <div>
                      <div className="font-semibold">今天</div>
                      <div className="text-sm text-gray-600">
                        完成 2 节课，观看 1 个视频
                      </div>
                    </div>
                  ),
                },
                {
                  color: 'blue',
                  children: (
                    <div>
                      <div className="font-semibold">昨天</div>
                      <div className="text-sm text-gray-600">
                        通过 3 次测验，学习 45 分钟
                      </div>
                    </div>
                  ),
                },
                {
                  color: 'gray',
                  children: (
                    <div>
                      <div className="font-semibold">本周</div>
                      <div className="text-sm text-gray-600">
                        完成 8 节课，学习 5 小时
                      </div>
                    </div>
                  ),
                },
              ]}
            />

            <Card size="small" className="mt-4 bg-blue-50">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">
                  {Math.round((lessonProgress + videoProgress + quizProgress) / 3)}%
                </div>
                <div className="text-sm text-gray-600">总体进度</div>
              </div>
            </Card>

            <div className="mt-4 text-center">
              <Button type="primary" block size="large">
                <ThunderboltOutlined /> 继续学习
              </Button>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
