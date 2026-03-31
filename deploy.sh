#!/bin/bash
# AI 学习系统 Web 前端部署脚本

set -e

echo "🚀 开始部署 AI 学习系统 Web 前端..."

# 1. 安装依赖
echo "📦 安装依赖..."
npm install

# 2. 构建项目
echo "🔨 构建项目..."
npm run build

# 3. 检查构建输出
if [ ! -d "dist" ]; then
    echo "❌ 构建失败：dist 目录不存在"
    exit 1
fi

echo "✅ 构建成功！"
echo ""
echo "📁 构建输出目录：$(pwd)/dist"
echo ""
echo "🌐 部署选项："
echo "  1. 本地预览：npm run preview"
echo "  2. Vercel 部署：vercel --prod"
echo "  3. Netlify 部署：netlify deploy --prod"
echo "  4. Nginx 部署：将 dist 内容复制到 Nginx 站点目录"
echo ""
echo "🔧 Nginx 配置示例："
cat << 'EOF'
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/ai-learning-web/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF
