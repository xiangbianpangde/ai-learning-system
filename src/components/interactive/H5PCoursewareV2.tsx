/**
 * H5P 互动课件组件 v2
 * 支持多种互动题型：选择题、填空题、拖拽匹配、时间线、热点图
 * 新增功能:
 * - 时间线题型
 * - 热点图题型
 * - 导出功能 (JSON/PDF)
 * - 更好的反馈机制
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Progress,
  Space,
  Result,
  Radio,
  Input,
  message,
  Collapse,
  Rate,
  Modal,
  Tooltip,
  Timeline,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  RedoOutlined,
  TrophyOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  AudioOutlined,
  StarOutlined,
} from '@ant-design/icons';
import { Stage, Layer, Circle, Rect, Text as KonvaText } from 'react-konva';

const { Panel } = Collapse;

// 题型定义
export type QuestionType = 'multiple-choice' | 'fill-blank' | 'drag-drop' | 'timeline' | 'hotspot';

export interface Question {
  id: string;
  type: QuestionType;
  title: string;
  content: string;
  options?: string[];
  correctAnswer: string | string[] | number | TimelineEvent[] | HotspotPoint[];
  feedback?: string;
  points: number;
  // 时间线特有
  events?: TimelineEvent[];
  // 热点图特有
  imageUrl?: string;
  hotspotPoints?: HotspotPoint[];
}

export interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  description: string;
}

export interface HotspotPoint {
  id: string;
  x: number;
  y: number;
  label: string;
  radius: number;
}

export interface InteractiveCourseware {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  passingScore: number;
}

interface H5PCoursewareProps {
  courseware: InteractiveCourseware;
  onComplete?: (score: number, totalPoints: number) => void;
  enableExport?: boolean;
  enableRecording?: boolean;
}

const H5PCourseware: React.FC<H5PCoursewareProps> = ({ 
  courseware, 
  onComplete,
  enableExport = true,
  enableRecording = false,
}) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [totalPoints, setTotalPoints] = useState(0);
  const [showExportModal, setShowExportModal] = useState(false);
  const [recording, setRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const currentQuestion = courseware.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / courseware.questions.length) * 100;

  // 计算总分
  useEffect(() => {
    const total = courseware.questions.reduce((sum, q) => sum + q.points, 0);
    setTotalPoints(total);
  }, [courseware.questions]);

  // 录音计时器
  useEffect(() => {
    if (recording) {
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
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
  }, [recording]);

  // 处理答案提交
  const handleSubmitAnswer = (answer: any) => {
    setAnswers({ ...answers, [currentQuestion.id]: answer });
    
    const isCorrect = checkAnswer(currentQuestion, answer);
    
    if (isCorrect) {
      setScore(score + currentQuestion.points);
      message.success('✅ 回答正确！');
    } else {
      message.error('❌ 再想想看~');
    }

    if (currentQuestionIndex < courseware.questions.length - 1) {
      setTimeout(() => {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }, 1000);
    } else {
      setTimeout(() => {
        setShowResult(true);
        const finalScore = score + (isCorrect ? currentQuestion.points : 0);
        setScore(finalScore);
        onComplete?.(finalScore, totalPoints);
      }, 1500);
    }
  };

  // 检查答案
  const checkAnswer = (question: Question, answer: any): boolean => {
    if (Array.isArray(question.correctAnswer)) {
      return JSON.stringify(answer.sort()) === JSON.stringify(question.correctAnswer.sort());
    }
    return answer === question.correctAnswer;
  };

  // 重新开始
  const handleRestart = () => {
    setCurrentQuestionIndex(0);
    setAnswers({});
    setShowResult(false);
    setScore(0);
    setRecordingTime(0);
  };

  // 导出功能
  const handleExport = (format: 'json' | 'pdf') => {
    if (format === 'json') {
      const exportData = {
        courseware: {
          id: courseware.id,
          title: courseware.title,
          totalQuestions: courseware.questions.length,
          passingScore: courseware.passingScore,
        },
        result: {
          score,
          totalPoints,
          percentage: ((score / totalPoints) * 100).toFixed(2),
          answers,
          completedAt: new Date().toISOString(),
        },
      };
      
      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${courseware.id}-result.json`;
      a.click();
      URL.revokeObjectURL(url);
      message.success('导出成功！');
    }
    setShowExportModal(false);
  };

  // 录音功能
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.start();
      setRecording(true);
      message.info('🎤 录音已开始');
    } catch (error) {
      message.error('无法访问麦克风');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setRecording(false);
      
      const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
      const url = URL.createObjectURL(audioBlob);
      const audio = new Audio(url);
      audio.play();
      
      message.success('🎤 录音已完成');
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // 渲染不同题型
  const renderQuestion = () => {
    switch (currentQuestion.type) {
      case 'multiple-choice':
        return <MultipleChoiceQuestion question={currentQuestion} onSubmit={handleSubmitAnswer} />;
      case 'fill-blank':
        return <FillBlankQuestion question={currentQuestion} onSubmit={handleSubmitAnswer} />;
      case 'drag-drop':
        return <DragDropQuestion question={currentQuestion} onSubmit={handleSubmitAnswer} />;
      case 'timeline':
        return <TimelineQuestion question={currentQuestion} onSubmit={handleSubmitAnswer} />;
      case 'hotspot':
        return <HotspotQuestion question={currentQuestion} onSubmit={handleSubmitAnswer} />;
      default:
        return <div>题型开发中...</div>;
    }
  };

  if (showResult) {
    const percentage = (score / totalPoints) * 100;
    const passed = percentage >= courseware.passingScore;

    return (
      <Card className="text-center">
        <Result
          icon={passed ? <TrophyOutlined style={{ color: '#faad14' }} /> : <RedoOutlined />}
          title={passed ? '🎉 恭喜通过！' : '💪 继续加油！'}
          subTitle={
            <div>
              <div className="text-2xl font-bold mb-2">
                得分：{score} / {totalPoints} ({percentage.toFixed(0)}%)
              </div>
              <Progress
                percent={percentage}
                status={passed ? 'success' : 'normal'}
                strokeColor={passed ? '#52c41a' : '#faad14'}
              />
              {passed && percentage >= 90 && (
                <div className="text-green-600 mt-2">
                  <StarOutlined /> 优秀表现！
                </div>
              )}
              {enableRecording && (
                <div className="mt-4 text-gray-600">
                  录音时长：{formatTime(recordingTime)}
                </div>
              )}
            </div>
          }
          extra={
            <Space>
              <Button onClick={handleRestart} icon={<RedoOutlined />}>
                重新开始
              </Button>
              {enableExport && (
                <Button 
                  icon={<DownloadOutlined />}
                  onClick={() => setShowExportModal(true)}
                >
                  导出结果
                </Button>
              )}
              <Button type="primary">查看解析</Button>
            </Space>
          }
        />
      </Card>
    );
  }

  return (
    <Card
      title={`📚 ${courseware.title}`}
      extra={
        <Space>
          <span>进度：{currentQuestionIndex + 1} / {courseware.questions.length}</span>
          <span>得分：{score}</span>
          {enableExport && (
            <Tooltip title="导出结果">
              <Button 
                type="text" 
                icon={<DownloadOutlined />} 
                onClick={() => setShowExportModal(true)}
              />
            </Tooltip>
          )}
          {enableRecording && (
            <Tooltip title={recording ? '停止录音' : '开始录音'}>
              <Button
                type={recording ? 'primary' : 'default'}
                icon={recording ? <PauseCircleOutlined /> : <AudioOutlined />}
                onClick={recording ? stopRecording : startRecording}
              />
            </Tooltip>
          )}
        </Space>
      }
    >
      <Progress percent={progress} showInfo={false} className="mb-4" />

      {enableRecording && (
        <div className="mb-4 text-center">
          <Space>
            <span>🎤 录音中:</span>
            <span className={`font-mono ${recording ? 'text-red-500' : 'text-gray-500'}`}>
              {formatTime(recordingTime)}
            </span>
          </Space>
        </div>
      )}

      <div className="min-h-[400px]">{renderQuestion()}</div>

      <Collapse className="mt-4">
        <Panel header="💡 提示" key="hint">
          <p>仔细阅读题目，选择或填写最合适的答案。</p>
          <p>每题答对可获得相应分数，最终得分达到 {courseware.passingScore}% 即可通过。</p>
        </Panel>
        {currentQuestion.feedback && (
          <Panel header="📖 解析" key="feedback">
            <p>{currentQuestion.feedback}</p>
          </Panel>
        )}
      </Collapse>

      {/* 导出模态框 */}
      <Modal
        title="导出结果"
        open={showExportModal}
        onCancel={() => setShowExportModal(false)}
        footer={null}
      >
        <div className="space-y-3">
          <Button 
            block 
            icon={<DownloadOutlined />}
            onClick={() => handleExport('json')}
          >
            导出为 JSON
          </Button>
          <Button 
            block 
            icon={<DownloadOutlined />}
            onClick={() => message.info('PDF 导出功能开发中...')}
          >
            导出为 PDF (开发中)
          </Button>
        </div>
      </Modal>
    </Card>
  );
};

// 选择题组件
interface MultipleChoiceQuestionProps {
  question: Question;
  onSubmit: (answer: string) => void;
}

const MultipleChoiceQuestion: React.FC<MultipleChoiceQuestionProps> = ({
  question,
  onSubmit,
}) => {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>

      <Radio.Group
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        className="flex flex-col gap-3"
      >
        {question.options?.map((option, index) => (
          <Radio.Button
            key={index}
            value={option}
            className="p-4 h-auto text-base"
          >
            {option}
          </Radio.Button>
        ))}
      </Radio.Group>

      <Button
        type="primary"
        size="large"
        className="mt-6"
        disabled={!selected}
        onClick={() => selected && onSubmit(selected)}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

// 填空题组件
interface FillBlankQuestionProps {
  question: Question;
  onSubmit: (answer: string) => void;
}

const FillBlankQuestion: React.FC<FillBlankQuestionProps> = ({
  question,
  onSubmit,
}) => {
  const [answer, setAnswer] = useState('');

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>

      <Input
        size="large"
        placeholder="请输入答案"
        value={answer}
        onChange={(e) => setAnswer(e.target.value)}
        onPressEnter={() => answer && onSubmit(answer)}
        className="mb-4"
      />

      <Button
        type="primary"
        size="large"
        disabled={!answer.trim()}
        onClick={() => onSubmit(answer.trim())}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

// 拖拽匹配题组件
interface DragDropQuestionProps {
  question: Question;
  onSubmit: (answer: string[]) => void;
}

const DragDropQuestion: React.FC<DragDropQuestionProps> = ({
  question,
  onSubmit,
}) => {
  // 简化实现，实际应使用 @hello-pangea/dnd
  const [selected, setSelected] = useState<string[]>([]);

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>
      <p className="text-sm text-gray-500 mb-4">拖拽功能演示：点击选项进行选择</p>

      <Space direction="vertical" className="w-full">
        {question.options?.map((option, index) => (
          <Button
            key={index}
            type={selected.includes(option) ? 'primary' : 'default'}
            onClick={() => {
              if (selected.includes(option)) {
                setSelected(selected.filter(s => s !== option));
              } else {
                setSelected([...selected, option]);
              }
            }}
            className="w-full text-left"
          >
            {option}
          </Button>
        ))}
      </Space>

      <Button
        type="primary"
        size="large"
        className="mt-6"
        disabled={selected.length === 0}
        onClick={() => onSubmit(selected)}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

// 时间线题型组件
interface TimelineQuestionProps {
  question: Question;
  onSubmit: (answer: TimelineEvent[]) => void;
}

const TimelineQuestion: React.FC<TimelineQuestionProps> = ({
  question,
  onSubmit,
}) => {
  const [orderedEvents, setOrderedEvents] = useState<TimelineEvent[]>(
    question.events ? [...question.events].sort(() => Math.random() - 0.5) : []
  );

  const moveEvent = (fromIndex: number, toIndex: number) => {
    const newEvents = [...orderedEvents];
    const [removed] = newEvents.splice(fromIndex, 1);
    newEvents.splice(toIndex, 0, removed);
    setOrderedEvents(newEvents);
  };

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>
      <p className="text-sm text-blue-600 mb-4">📅 请按时间顺序排列以下事件</p>

      <Timeline
        items={orderedEvents.map((event, index) => ({
          children: (
            <div>
              <div className="font-medium">{event.title}</div>
              <div className="text-sm text-gray-500">{event.description}</div>
              <div className="text-xs text-gray-400 mt-1">{event.date}</div>
              <Space className="mt-2">
                <Button
                  size="small"
                  disabled={index === 0}
                  onClick={() => moveEvent(index, index - 1)}
                >
                  ↑ 上移
                </Button>
                <Button
                  size="small"
                  disabled={index === orderedEvents.length - 1}
                  onClick={() => moveEvent(index, index + 1)}
                >
                  ↓ 下移
                </Button>
              </Space>
            </div>
          ),
          color: 'blue',
        }))}
      />

      <Button
        type="primary"
        size="large"
        className="mt-6"
        onClick={() => onSubmit(orderedEvents)}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

// 热点图题型组件
interface HotspotQuestionProps {
  question: Question;
  onSubmit: (answer: HotspotPoint[]) => void;
}

const HotspotQuestion: React.FC<HotspotQuestionProps> = ({
  question,
  onSubmit,
}) => {
  const [selectedPoints, setSelectedPoints] = useState<HotspotPoint[]>([]);
  const stageRef = useRef<any>(null);

  const handleStageClick = (e: any) => {
    const stage = e.target.getStage();
    const point = stage.getPointerPosition();
    
    if (point) {
      const newPoint: HotspotPoint = {
        id: `point-${Date.now()}`,
        x: point.x,
        y: point.y,
        label: `标记 ${selectedPoints.length + 1}`,
        radius: 20,
      };
      setSelectedPoints([...selectedPoints, newPoint]);
    }
  };

  const removePoint = (index: number) => {
    setSelectedPoints(selectedPoints.filter((_, i) => i !== index));
  };

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>
      <p className="text-sm text-blue-600 mb-4">📍 点击图片标注正确位置</p>

      <div className="border rounded-lg overflow-hidden mb-4">
        <Stage
          ref={stageRef}
          width={600}
          height={400}
          onClick={handleStageClick}
          style={{ background: '#f0f0f0' }}
        >
          <Layer>
            {/* 背景图像占位 */}
            <Rect x={0} y={0} width={600} height={400} fill="#e8e8e8" />
            <KonvaText
              x={250}
              y={190}
              text="点击此处标注"
              fontSize={16}
              fill="#999"
            />
            
            {/* 已选择的点 */}
            {selectedPoints.map((point, index) => (
              <React.Fragment key={point.id}>
                <Circle
                  x={point.x}
                  y={point.y}
                  radius={point.radius}
                  fill="rgba(24, 144, 255, 0.3)"
                  stroke="#1890ff"
                  strokeWidth={2}
                />
                <KonvaText
                  x={point.x - 20}
                  y={point.y - 35}
                  text={point.label}
                  fontSize={12}
                  fill="#1890ff"
                />
              </React.Fragment>
            ))}
          </Layer>
        </Stage>
      </div>

      {selectedPoints.length > 0 && (
        <div className="mb-4">
          <p className="text-sm font-medium mb-2">已标注位置:</p>
          <Space>
            {selectedPoints.map((point, index) => (
              <Tag key={point.id} closable onClose={() => removePoint(index)}>
                {point.label} ({Math.round(point.x)}, {Math.round(point.y)})
              </Tag>
            ))}
          </Space>
        </div>
      )}

      <Button
        type="primary"
        size="large"
        className="mt-6"
        disabled={selectedPoints.length === 0}
        onClick={() => onSubmit(selectedPoints)}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

export default H5PCourseware;
