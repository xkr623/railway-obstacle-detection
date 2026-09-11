<template>
  <div class="card">
    <h2>Video Detection</h2>

    <!-- 上传 -->
    <input type="file" accept="video/*" @change="onFileChange" />

    <button :disabled="!videoFile || loading" @click="uploadVideo">
      {{ loading ? 'Processing...' : 'Upload & Detect' }}
    </button>

    <p v-if="loading" class="loading">
      Processing video, please wait...
    </p>

    <!-- 结果区域 -->
    <div v-if="videoUrl" class="result-container">
      <!-- 左侧视频 -->
      <video
        ref="video"
        :src="videoUrl"
        controls
        class="result-video"
        @loadedmetadata="onVideoReady"
      ></video>

      <!-- 右侧结果面板 -->
      <div class="result-panel">
        <h3>Detection Results</h3>

        <!-- 类别筛选 -->
        <div class="filter">
          <label>Filter:</label>
          <select v-model="selectedClass">
            <option value="">All</option>
            <option v-for="cls in classOptions" :key="cls" :value="cls">
              {{ cls }}
            </option>
          </select>
        </div>

        <div v-if="filteredObjects.length === 0" class="empty">
          No objects
        </div>

        <!-- 表头（固定） -->
        <div v-else class="list-header">
          <span class="col-cls">Class</span>
          <span class="col-time">Time(s)</span>
          <span class="col-conf">Conf</span>
          <span class="col-box">xmin</span>
          <span class="col-box">ymin</span>
          <span class="col-box">xmax</span>
          <span class="col-box">ymax</span>
        </div>

        <!-- 列表（滚动） -->
        <ul class="object-list">
          <li
            v-for="(obj, index) in filteredObjects"
            :key="index"
            @click="jumpTo(obj.time)"
          >
            <span class="col-cls">{{ obj.cls_name }}</span>
            <span class="col-time">{{ obj.time.toFixed(2) }}</span>
            <span class="col-conf">{{ obj.conf.toFixed(2) }}</span>
            <span class="col-box">{{ obj.xmin }}</span>
            <span class="col-box">{{ obj.ymin }}</span>
            <span class="col-box">{{ obj.xmax }}</span>
            <span class="col-box">{{ obj.ymax }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import request from "../api/request";

export default {
  name: "VideoUpload",

  data() {
    return {
      videoFile: null,
      videoUrl: "",
      objects: [],
      loading: false,

      videoReady: false,
      selectedClass: "",
    };
  },

  computed: {
    classOptions() {
      return [...new Set(this.objects.map(o => o.cls_name))];
    },

    filteredObjects() {
      if (!this.selectedClass) return this.objects;
      return this.objects.filter(
        o => o.cls_name === this.selectedClass
      );
    },
  },

  methods: {
    onFileChange(e) {
      this.videoFile = e.target.files[0];
      this.videoUrl = "";
      this.objects = [];
      this.videoReady = false;
      this.selectedClass = "";
    },

    async uploadVideo() {
      this.loading = true;
      const formData = new FormData();
      formData.append("file", this.videoFile);

      try {
        const res = await request.post("/detect/video", formData);

        this.videoUrl =
          request.defaults.baseURL + res.data.video_url;

        this.objects = res.data.objects || [];
      } catch (e) {
        console.error(e);
        alert("Video detection failed");
      } finally {
        this.loading = false;
      }
    },

    onVideoReady() {
      this.videoReady = true;
    },

    jumpTo(time) {
      const video = this.$refs.video;
      if (!video) return;

      if (!this.videoReady) {
        video.addEventListener(
          "loadedmetadata",
          () => {
            video.currentTime = time;
            video.play();
          },
          { once: true }
        );
      } else {
        video.currentTime = time;
        video.play();
      }
    },
  },
};
</script>

<style scoped>
.card {
  background: white;
  padding: 24px;
  border-radius: 16px;
}

h2 {
  text-align: center;
  color: #1677ff;
}

button {
  margin-top: 15px;
  padding: 10px 26px;
  border-radius: 24px;
  border: none;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  color: white;
  cursor: pointer;
}

.loading {
  margin-top: 12px;
  text-align: center;
  color: #999;
}

/* 布局 */
.result-container {
  margin-top: 24px;
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.result-video {
  width: 720px;
  height: 405px;
  background: black;
  border-radius: 12px;
  object-fit: contain;
}

/* 右侧 */
.result-panel {
  width: 420px;
  max-height: 405px;
  border-left: 1px solid #eee;
  padding-left: 12px;
  display: flex;
  flex-direction: column;
}

.filter {
  margin-bottom: 10px;
  font-size: 13px;
}

.filter select {
  width: 100%;
}

/* 表头 */
.list-header {
  display: flex;
  gap: 6px;
  font-size: 12px;
  font-weight: bold;
  padding: 6px 4px;
  background: #f0f5ff;
  border-radius: 6px;
  position: sticky;
  top: 0;
  z-index: 2;
}

/* 列表 */
.object-list {
  list-style: none;
  padding: 0;
  margin: 6px 0 0;
  overflow-y: auto;
  flex: 1;
}

.object-list li {
  display: flex;
  gap: 6px;
  padding: 6px 4px;
  font-size: 12px;
  background: #f5f9ff;
  margin-bottom: 6px;
  border-radius: 6px;
  cursor: pointer;
}

.object-list li:hover {
  background: #e6f0ff;
}

/* 列宽 */
.col-cls {
  width: 60px;
  font-weight: bold;
  color: #1677ff;
}

.col-time {
  width: 55px;
}

.col-conf {
  width: 45px;
  color: #999;
}

.col-box {
  width: 50px;
  font-family: monospace;
  color: #666;
}

.empty {
  color: #aaa;
  font-size: 13px;
}
</style>
