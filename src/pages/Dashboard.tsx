import React, { useEffect } from 'react';
import { Card, Row, Col, Progress, Statistic, Table, Typography, Tag } from 'antd';
import {
  BookOutlined,
  CheckCircleOutlined,
  FireOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import { useLearningStore } from '../store';
import { learningApi } from '../services/api';
import type { LearningProgress } from '../types';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const { progress, stats, setProgress, setStats, setLoading } = useLearningStore();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [progressData, statsData] = await Promise.all([
          learningApi.getProgress(),
          learningApi.getStats(),
        ]);
        setProgress(progressData);
        setStats(statsData);
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const progressColumns = [
    {
      title: '课程名称',
      dataIndex: 'courseName',
      key: 'courseName',
      render: (text: string) => <Text strong>{text}</Text>,
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
      ),
    },
    {
      title: '完成情况',
      key: 'lessons',
      render: (_: any, record: LearningProgress) => (
        <Tag color="blue">
          {record.completedLessons}/{record.totalLessons} 课时
        </Tag>
      ),
    },
    {
      title: '最近学习',
      dataIndex: 'lastLearnedAt',
      key: 'lastLearnedAt',
      render: (date: string) => new Date(date).toLocaleDateString('zh-CN'),
    },
  ];

  return (
    <div className="p-6">
      <Title level={2} className="mb-6">📊 学习仪表盘</Title>

      {/* 统计卡片 */}
      <Row gutter={[16, 16]} className="mb-6">
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="总学习时长"
              value={stats?.totalLearningTime || 0}
              suffix="分钟"
              prefix={<ClockCircleOutlined className="text-blue-500" />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="完成课程"
              value={stats?.coursesCompleted || 0}
              suffix="门"
              prefix={<BookOutlined className="text-green-500" />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="完成练习"
              value={stats?.exercisesCompleted || 0}
              suffix="题"
              prefix={<CheckCircleOutlined className="text-purple-500" />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="dashboard-card">
            <Statistic
              title="连续学习"
              value={stats?.streakDays || 0}
              suffix="天"
              prefix={<FireOutlined className="text-orange-500" />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 平均分 */}
      {stats && (
        <Row gutter={16} className="mb-6">
          <Col span={24}>
            <Card className="dashboard-card">
              <div className="flex items-center justify-between">
                <div>
                  <Text type="secondary">平均得分</Text>
                  <div className="text-3xl font-bold text-orange-500">
                    {stats.averageScore.toFixed(1)}%
                  </div>
                </div>
                <TrophyOutlined className="text-4xl text-yellow-500" />
              </div>
              <Progress
                percent={stats.averageScore}
                strokeColor="#faad14"
                className="mt-4"
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 学习进度表格 */}
      <Card title="📚 课程进度" className="dashboard-card">
        <Table
          columns={progressColumns}
          dataSource={progress}
          rowKey="courseId"
          pagination={false}
          loading={!stats}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
