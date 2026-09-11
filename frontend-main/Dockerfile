# ============================================================
# 前端镜像：多阶段构建
#   stage 1 (build)  : Node 环境编译 Vite 静态资源
#   stage 2 (deploy) : Nginx 托管静态文件并反向代理后端
# ============================================================

# ---------- Stage 1: 构建 ----------
FROM node:20-alpine AS build

WORKDIR /app

# 先拷贝依赖清单，利用 Docker 层缓存（代码变动不会重新 npm install）
COPY package*.json ./
# 使用国内 npm 镜像加速构建
RUN npm config set registry https://registry.npmmirror.com \
    && npm install

# 拷贝源码并构建（产物在 /app/dist）
COPY . .
RUN npm run build

# ---------- Stage 2: 运行 ----------
FROM nginx:alpine

# 自定义 Nginx 配置（SPA + API 反代 + WebSocket）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 从构建阶段拷贝静态资源
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
