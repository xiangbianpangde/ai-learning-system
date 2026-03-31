/**
 * H5P 互动课件组件
 * 支持多种互动题型：选择题、填空题、拖拽匹配、时间线等
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Progress,
  Space,
  Result,
  Radio,
  Input,
  DragDropContext,
  Droppable,
  Draggable,
  message,
  Collapse,
  Rate,
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  RedoOutlined,
  TrophyOutlined,
} from '@ant-design/icons';
import type { DropResult } from '@hello-pangea/dnd';

const { Panel } = Collapse;

// 题型定义
export type QuestionType = 'multiple-choice' | 'fill-blank' | 'drag-drop' | 'timeline' | 'hotspot';

export interface Question {
  id: string;
  type: QuestionType;
  title: string;
  content: string;
  options?: string[];
  correctAnswer: string | string[];
  feedback?: string;
  points: number;
}

export interface InteractiveCourseware {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  passingScore: number; // 及格线百分比
}

interface H5PCoursewareProps {
  courseware: InteractiveCourseware;
  onComplete?: (score: number, totalPoints: number) => void;
}

const H5PCourseware: React.FC<H5PCoursewareProps> = ({ courseware, onComplete }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [showResult, setShowResult] = useState(false);
  const [score, setScore] = useState(0);
  const [totalPoints, setTotalPoints] = useState(0);

  const currentQuestion = courseware.questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / courseware.questions.length) * 100;

  // 计算总分
  useEffect(() => {
    const total = courseware.questions.reduce((sum, q) => sum + q.points, 0);
    setTotalPoints(total);
  }, [courseware.questions]);

  // 处理答案提交
  const handleSubmitAnswer = (answer: any) => {
    setAnswers({ ...answers, [currentQuestion.id]: answer });
    
    // 检查答案
    const isCorrect = checkAnswer(currentQuestion, answer);
    
    if (isCorrect) {
      setScore(score + currentQuestion.points);
      message.success('✅ 回答正确！');
    } else {
      message.error('❌ 再想想看~');
    }

    // 下一题或显示结果
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
  };

  // 渲染不同题型
  const renderQuestion = () => {
    switch (currentQuestion.type) {
      case 'multiple-choice':
        return (
          <MultipleChoiceQuestion
            question={currentQuestion}
            onSubmit={handleSubmitAnswer}
          />
        );
      case 'fill-blank':
        return (
          <FillBlankQuestion
            question={currentQuestion}
            onSubmit={handleSubmitAnswer}
          />
        );
      case 'drag-drop':
        return (
          <DragDropQuestion
            question={currentQuestion}
            onSubmit={handleSubmitAnswer}
          />
        );
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
                <div className="text-green-600 mt-2">🌟 优秀表现！</div>
              )}
            </div>
          }
          extra={
            <Space>
              <Button onClick={handleRestart} icon={<RedoOutlined />}>
                重新开始
              </Button>
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
          <span>
            进度：{currentQuestionIndex + 1} / {courseware.questions.length}
          </span>
          <span>得分：{score}</span>
        </Space>
      }
    >
      <Progress percent={progress} showInfo={false} className="mb-4" />

      <div className="min-h-[400px]">{renderQuestion()}</div>

      <Collapse className="mt-4">
        <Panel header="💡 提示" key="hint">
          <p>仔细阅读题目，选择或填写最合适的答案。</p>
          <p>每题答对可获得相应分数，最终得分达到 {courseware.passingScore}% 即可通过。</p>
        </Panel>
      </Collapse>
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
  const [items, setItems] = useState([
    { id: '1', content: '选项 A' },
    { id: '2', content: '选项 B' },
    { id: '3', content: '选项 C' },
  ]);
  const [droppedItems, setDroppedItems] = useState<any[]>([]);

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;

    const sourceArray = result.source.droppableId === 'source' ? items : droppedItems;
    const destArray = result.destination.droppableId === 'source' ? items : droppedItems;

    const [removed] = sourceArray.splice(result.source.index, 1);
    destArray.splice(result.destination.index, 0, removed);

    setItems([...items]);
    setDroppedItems([...droppedItems]);
  };

  const handleSubmit = () => {
    const answer = droppedItems.map((item) => item.id);
    onSubmit(answer);
  };

  return (
    <div>
      <h3 className="text-xl font-semibold mb-4">{question.title}</h3>
      <p className="text-gray-600 mb-6">{question.content}</p>

      <div className="flex gap-8">
        <div className="flex-1">
          <h4 className="mb-2 font-medium">拖拽区</h4>
          <Droppable droppableId="source">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="border-2 border-dashed border-gray-300 rounded-lg p-4 min-h-[200px]"
              >
                {items.map((item, index) => (
                  <Draggable key={item.id} draggableId={item.id} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        className="bg-white border rounded p-3 mb-2 cursor-move shadow-sm"
                      >
                        {item.content}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </div>

        <div className="flex-1">
          <h4 className="mb-2 font-medium">答案区</h4>
          <Droppable droppableId="target">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                className="border-2 border-dashed border-blue-300 rounded-lg p-4 min-h-[200px]"
              >
                {droppedItems.map((item, index) => (
                  <Draggable key={item.id} draggableId={item.id} index={index}>
                    {(provided) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        {...provided.dragHandleProps}
                        className="bg-blue-50 border border-blue-200 rounded p-3 mb-2 cursor-move"
                      >
                        {item.content}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </div>
      </div>

      <Button
        type="primary"
        size="large"
        className="mt-6"
        onClick={handleSubmit}
        icon={<CheckCircleOutlined />}
      >
        提交答案
      </Button>
    </div>
  );
};

export default H5PCourseware;
