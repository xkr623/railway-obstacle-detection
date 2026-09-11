# ============================================================
# 后端镜像：FastAPI + YOLO(ultralytics) 铁路障碍物检测服务
# 基础镜像选用 slim 变体 + CPU 版 PyTorch，控制镜像体积
# ============================================================
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # 国内 PyPI 主源（清华），加速常规依赖下载
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    # 额外源：PyTorch CPU wheel（pip 会优先从清华找 torch，找不到再去这里）
    PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu

# OpenCV 运行时依赖（libGL / libGLib）；
# ffmpeg 用于把 OpenCV 输出的 mp4v 视频转码为浏览器兼容的 H.264
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 工作目录与本地开发保持一致（app.py 用相对路径引用模型权重）
WORKDIR /app

# 模型权重放在上级目录，匹配 app.py 里的 ../railway_obstacles_detection/...
COPY railway_obstacles_detection/runs/detect/train/weights/best.pt \
     /app/railway_obstacles_detection/runs/detect/train/weights/best.pt

# 拷贝后端源码
WORKDIR /app/raliway-main
COPY backend/ ./backend/

# 一次性装完所有依赖（torch/torchvision 由 pip 自动匹配 CPU 源，不再硬编码版本号）
RUN pip install -r backend/requirements.txt

EXPOSE 8000

# 启动时会自动加载并预热 YOLO 模型（约需 30~60 秒）
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
