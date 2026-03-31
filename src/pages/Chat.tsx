import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Input,
  Button,
  List,
  Avatar,
  Typography,
  Spin,
  Empty,
} from 'antd';
import {
  SendOutlined,
  PlusOutlined,
  MessageOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import { useChatStore } from '../store';
import { chatApi } from '../services/api';
import type { ChatMessage as ChatMessageType } from '../types';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const Chat: React.FC = () => {
  const {
    sessions,
    currentSessionId,
    isLoading,
    createSession,
    setCurrentSession,
    addMessage,
    deleteSession,
    setLoading,
  } = useChatStore();

  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentSession = sessions.find((s) => s.id === currentSessionId);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentSession?.messages]);

  const handleCreateSession = async () => {
    try {
      const result = await chatApi.createSession('新对话');
      createSession(result.id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !currentSessionId) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    addMessage(currentSessionId, { role: 'user', content: userMessage });
    setLoading(true);

    try {
      const response = await chatApi.sendMessage(currentSessionId, userMessage);
      addMessage(currentSessionId, { role: 'assistant', content: response.content });
    } catch (error) {
      addMessage(currentSessionId, {
        role: 'system',
        content: '发送失败，请重试',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await chatApi.deleteSession(sessionId);
      deleteSession(sessionId);
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  return (
    <div className="p-6 h-screen flex gap-4">
      {/* 侧边栏 - 对话列表 */}
      <Card className="w-64 flex-shrink-0 flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <Title level={4} className="!mb-0">💬 对话历史</Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            size="small"
            onClick={handleCreateSession}
          />
        </div>
        <List
          dataSource={sessions}
          renderItem={(session) => (
            <List.Item
              className={`cursor-pointer hover:bg-gray-50 p-2 rounded ${
                session.id === currentSessionId ? 'bg-blue-50' : ''
              }`}
              onClick={() => setCurrentSession(session.id)}
              actions={[
                <Button
                  key="more"
                  type="text"
                  size="small"
                  icon={<MoreOutlined />}
                  onClick={() => handleDeleteSession(session.id)}
                />,
              ]}
            >
              <List.Item.Meta
                avatar={<Avatar icon={<MessageOutlined />} />}
                title={<Text ellipsis>{session.title || '新对话'}</Text>}
                description={
                  <Text type="secondary" className="text-xs">
                    {new Date(session.updatedAt).toLocaleDateString('zh-CN')}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      </Card>

      {/* 主聊天区域 */}
      <Card className="flex-1 flex flex-col">
        {currentSessionId ? (
          <>
            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto mb-4">
              {currentSession?.messages.length === 0 ? (
                <Empty description="开始和 AI 助手对话吧" />
              ) : (
                <div className="space-y-4">
                  {currentSession?.messages.map((msg: ChatMessageType) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] p-4 rounded-lg ${
                          msg.role === 'user'
                            ? 'bg-blue-500 text-white'
                            : msg.role === 'system'
                            ? 'bg-red-50 text-red-600'
                            : 'bg-gray-100'
                        }`}
                      >
                        <Paragraph
                          className={`!mb-0 ${
                            msg.role === 'user' ? 'text-white' : 'text-gray-800'
                          }`}
                        >
                          {msg.content}
                        </Paragraph>
                        <Text
                          className={`text-xs mt-2 block ${
                            msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'
                          }`}
                        >
                          {new Date(msg.createdAt).toLocaleTimeString('zh-CN')}
                        </Text>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 p-4 rounded-lg">
                        <Spin tip="AI 思考中..." />
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* 输入区域 */}
            <div className="flex gap-2">
              <TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="输入问题，按 Enter 发送..."
                autoSize={{ minRows: 2, maxRows: 4 }}
                disabled={isLoading}
              />
              <Button
                type="primary"
                icon={<SendOutlined />}
                size="large"
                onClick={handleSendMessage}
                loading={isLoading}
                disabled={!inputValue.trim()}
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <Empty
              description={
                <div>
                  <Text className="block mb-2">👋 开始新的对话</Text>
                  <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>
                    创建对话
                  </Button>
                </div>
              }
            />
          </div>
        )}
      </Card>
    </div>
  );
};

export default Chat;
