<template>
  <div class="card">
    <h2>Real-time Camera Detection</h2>

    <div v-if="!isRecognitionActive" class="placeholder">
      Camera is OFF
    </div>

    <canvas
      v-show="isRecognitionActive"
      ref="displayCanvas"
      width="640"
      height="480"
      @click="onCanvasClick"
    ></canvas>

    <video
      ref="video"
      width="640"
      height="480"
      autoplay
      muted
      playsinline
      style="display: none"
    ></video>

    <canvas
      ref="captureCanvas"
      width="640"
      height="480"
      style="display: none"
    ></canvas>

    <div class="controls">
      <button @click="startRecognition" :disabled="isRecognitionActive">
        Start
      </button>
      <button @click="stopRecognition" :disabled="!isRecognitionActive">
        Stop
      </button>
    </div>

    <div v-if="boxes.length" class="selector">
      <label>Select Target：</label>
      <select v-model="selectedIndex" @change="onSelectChange">
        <option :value="-1">All</option>
        <option v-for="(box, index) in boxes" :key="index" :value="index">
          {{ box.cls_name }}_{{ index }}
        </option>
      </select>
    </div>

    <div class="coords" v-if="currentBox">
      <h4>Current Target</h4>
      <p><b>Class:</b> {{ currentBox.cls_name }}</p>
      <p><b>Conf:</b> {{ currentBox.conf.toFixed(2) }}</p>
      <p><b>xmin:</b> {{ currentBox.xmin }}</p>
      <p><b>ymin:</b> {{ currentBox.ymin }}</p>
      <p><b>xmax:</b> {{ currentBox.xmax }}</p>
      <p><b>ymax:</b> {{ currentBox.ymax }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "RealtimeRecognition",

  data() {
    return {
      videoStream: null,
      socket: null,
      sendTimer: null,
      isRecognitionActive: false,

      boxes: [],
      currentBox: null,
      selectedIndex: -1,
    };
  },

  methods: {
    async startRecognition() {
      if (this.isRecognitionActive) return;
      this.isRecognitionActive = true;

      /* 1️⃣ 打开摄像头 */
      try {
        this.videoStream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480 },
        });
        this.$refs.video.srcObject = this.videoStream;
      } catch {
        alert("Camera access denied");
        this.isRecognitionActive = false;
        return;
      }

      /* 2️⃣ 等待 video 真正开始输出画面（关键修复点） */
      await new Promise((resolve) => {
        const video = this.$refs.video;
        video.onloadedmetadata = () => video.play();
        video.onplaying = () => resolve();
      });

      /* 3️⃣ WebSocket（地址跟随当前页面，自动适配 http/ws 与 https/wss） */
      const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
      this.socket = new WebSocket(
        `${wsProto}://${window.location.host}/ws/detect`
      );
      this.socket.binaryType = "arraybuffer";

      this.socket.onmessage = (event) => {
        /* JSON */
        if (typeof event.data === "string") {
          const data = JSON.parse(event.data);
          this.boxes = data.boxes || [];

          if (this.selectedIndex >= this.boxes.length) {
            this.selectedIndex = -1;
          }

          this.currentBox =
            this.selectedIndex === -1
              ? this.boxes[0] || null
              : this.boxes[this.selectedIndex] || null;

          return;
        }

        /* Binary Image */
        const blob = new Blob([event.data], { type: "image/jpeg" });
        const img = new Image();
        const url = URL.createObjectURL(blob);

        img.onload = () => {
          const ctx = this.$refs.displayCanvas.getContext("2d");
          ctx.clearRect(0, 0, 640, 480);
          ctx.drawImage(img, 0, 0, 640, 480);
          URL.revokeObjectURL(url);
        };

        img.src = url;
      };

      /* 4️⃣ 开始抓帧（此时 video 已经是“真画面”） */
      this.sendTimer = setInterval(() => {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) return;

        const ctx = this.$refs.captureCanvas.getContext("2d");
        ctx.drawImage(this.$refs.video, 0, 0, 640, 480);

        this.$refs.captureCanvas.toBlob((blob) => {
          if (!blob) return;
          blob.arrayBuffer().then((buf) => this.socket.send(buf));
        }, "image/jpeg");
      }, 200);
    },

    stopRecognition() {
      if (this.sendTimer) clearInterval(this.sendTimer);
      if (this.socket) this.socket.close();
      if (this.videoStream) {
        this.videoStream.getTracks().forEach((t) => t.stop());
      }

      const ctx = this.$refs.displayCanvas.getContext("2d");
      ctx.clearRect(0, 0, 640, 480);

      this.boxes = [];
      this.currentBox = null;
      this.selectedIndex = -1;
      this.isRecognitionActive = false;
    },

    onSelectChange() {
      this.currentBox =
        this.selectedIndex === -1
          ? this.boxes[0] || null
          : this.boxes[this.selectedIndex] || null;
    },

    onCanvasClick(e) {
      if (!this.boxes.length) return;

      const rect = this.$refs.displayCanvas.getBoundingClientRect();
      const x = ((e.clientX - rect.left) / rect.width) * 640;
      const y = ((e.clientY - rect.top) / rect.height) * 480;

      let min = Infinity;
      let idx = -1;

      this.boxes.forEach((b, i) => {
        const cx = (b.xmin + b.xmax) / 2;
        const cy = (b.ymin + b.ymax) / 2;
        const d = Math.hypot(cx - x, cy - y);
        if (d < min) {
          min = d;
          idx = i;
        }
      });

      this.selectedIndex = idx;
      this.currentBox = this.boxes[idx] || null;
    },
  },

  beforeUnmount() {
    this.stopRecognition();
  },
};
</script>

<style scoped>
.card {
  background: white;
  padding: 24px;
  border-radius: 16px;
  text-align: center;
}

.placeholder {
  width: 640px;
  height: 480px;
  border: 2px dashed #bcd3ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: auto;
}

canvas {
  margin: 10px auto;
  border-radius: 12px;
  cursor: crosshair;
}

.controls {
  margin-top: 12px;
}

.selector {
  margin-top: 12px;
}

.coords {
  margin-top: 16px;
  padding: 12px;
  background: #f5f9ff;
  border-radius: 10px;
  text-align: left;
}
</style>
