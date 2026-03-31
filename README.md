# AI 学习系统 Web 前端

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **UI 组件**: Ant Design 5.x
- **样式**: TailwindCSS 4.x
- **状态管理**: Zustand
- **HTTP 客户端**: Axios
- **数据请求**: React Query (TanStack Query)
- **路由**: React Router DOM 6.x

## 项目结构

```
ai-learning-web/
├── src/
│   ├── components/     # 可复用组件
│   │   ├── common/     # 通用组件
│   │   ├── user/       # 用户相关组件
│   │   ├── dashboard/  # 仪表盘组件
│   │   ├── chat/       # 对话组件
│   │   ├── course/     # 课程组件
│   │   └── exercise/   # 练习组件
│   ├── pages/          # 页面组件
│   │   ├── Login.tsx
│   │   ├── Register.tsx
│   │   ├── Dashboard.tsx
│   │   ├── Chat.tsx
│   │   ├── Course.tsx
│   │   ├── Lesson.tsx
│   │   └── Exercise.tsx
│   ├── hooks/          # 自定义 Hooks
│   ├── store/          # Zustand 状态管理
│   ├── services/       # API 服务
│   ├── types/          # TypeScript 类型定义
│   ├── utils/          # 工具函数
│   ├── App.tsx         # 主应用组件
│   ├── main.tsx        # 入口文件
│   └── index.css       # 全局样式
├── public/             # 静态资源
├── .env                # 环境变量
├── vite.config.ts      # Vite 配置
├── tsconfig.json       # TypeScript 配置
└── package.json        # 项目依赖
```

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
```

### 预览构建

```bash
npm run preview
```

## 核心模块

### 1. 用户系统
- 登录/注册页面
- JWT 认证
- 个人资料管理

### 2. 学习仪表盘
- 学习进度追踪
- 统计数据展示
- 课程进度表格

### 3. AI 对话界面
- 实时问答
- 对话历史管理
- 流式响应支持

### 4. 课程内容页
- 视频播放器
- 文本内容渲染
- 练习嵌入

### 5. 练习系统
- 多种题型支持
- 自动批改
- 详细反馈

## API 配置

在 `.env` 文件中配置后端 API 地址：

```env
VITE_API_BASE_URL=http://localhost:3001/api
```

## 开发规范

- 使用 TypeScript 严格模式
- 组件采用函数式 + Hooks
- 状态管理使用 Zustand
- 样式采用 TailwindCSS + Ant Design
- API 请求统一在 services 层处理

## 部署

构建后的 `dist` 目录可部署到任意静态托管服务：

- Vercel
- Netlify
- Cloudflare Pages
- Nginx

## License

MIT
