<template>
  <div id="app">
    <!-- Header -->
    <header class="app-header">
      <h1>YOLO Railway Obstacle Detection System</h1>
      <p>AI-based Object Detection · Real-time · Image · Video</p>
    </header>

    <!-- Main Content -->
    <main class="app-main">
      <ImageUpload />
      <VideoUpload />
      <RealtimeRecognition />
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <span>© 2025 YOLO Detection Platform</span>
      <span class="status-dot"></span>
      <span>System Running</span>
    </footer>
  </div>
</template>

<script>
import ImageUpload from './views/ImageUpload.vue';
import VideoUpload from './views/VideoUpload.vue';
import RealtimeRecognition from './views/RealtimeRecognition.vue';

export default {
  name: 'App',
  components: {
    ImageUpload,
    VideoUpload,
    RealtimeRecognition,
  },
};
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(180deg, #f4f8ff, #ffffff);
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  color: #1f2d3d;
}

/* Header */
.app-header {
  padding: 30px 20px;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  color: white;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.app-header h1 {
  margin: 0;
  font-size: 28px;
  letter-spacing: 1px;
}

.app-header p {
  margin-top: 8px;
  font-size: 14px;
  opacity: 0.9;
}

/* Main */
.app-main {
  max-width: 1200px;
  margin: 40px auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 40px;
  padding: 0 20px;
}

/* Footer */
.app-footer {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  padding: 15px;
  font-size: 13px;
  color: #666;
}

.status-dot {
  width: 8px;
  height: 8px;
  background: #52c41a;
  border-radius: 50%;
}
</style>
