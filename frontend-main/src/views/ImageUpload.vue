<template>
  <div class="card">
    <h2>Image Detection</h2>

    <input type="file" accept="image/*" @change="onFileChange" />

    <button @click="uploadImage" :disabled="loading">
      {{ loading ? "Detecting..." : "Start Detection" }}
    </button>

    <p v-if="loading" class="loading">Detecting image, please wait...</p>

    <!-- 检测结果 -->
    <div v-if="resultImg" class="result">
      <h3>Detection Result</h3>

      <!-- 点击图片选择最近目标 -->
      <img
        ref="imgRef"
        :src="resultImg"
        @click="onImageClick"
      />

      <!-- 下拉框选择目标 -->
      <div class="selector" v-if="boxes.length">
        <label>Select Target：</label>
        <select v-model="selectedIndex" @change="onSelectChange">
          <option :value="-1">All</option>
          <option
            v-for="(box, index) in boxes"
            :key="index"
            :value="index"
          >
            {{ box.cls_name }}_{{ index }}
          </option>
        </select>
      </div>

      <!-- 坐标显示 -->
      <div class="coords" v-if="currentBox">
        <h4>Current Target Coordinates</h4>
        <p><strong>xmin:</strong> {{ currentBox.xmin }}</p>
        <p><strong>ymin:</strong> {{ currentBox.ymin }}</p>
        <p><strong>xmax:</strong> {{ currentBox.xmax }}</p>
        <p><strong>ymax:</strong> {{ currentBox.ymax }}</p>
      </div>

      <div class="coords empty" v-else>
        <p>No object detected</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import request from "../api/request";

const file = ref(null);
const loading = ref(false);
const resultImg = ref(null);

const boxes = ref([]);          // 所有目标
const currentBox = ref(null);   // 当前选中目标
const selectedIndex = ref(0);   // 下拉框索引

const imgRef = ref(null);

const onFileChange = (e) => {
  file.value = e.target.files[0];
  resultImg.value = null;
  boxes.value = [];
  currentBox.value = null;
  selectedIndex.value = 0;
};

const uploadImage = async () => {
  if (!file.value) {
    alert("Please select an image first");
    return;
  }

  const formData = new FormData();
  formData.append("file", file.value);

  loading.value = true;

  try {
    const res = await request.post("/detect/image", formData);

    resultImg.value =
      request.defaults.baseURL + res.data.image_url;

    boxes.value = res.data.boxes || [];

    // 默认第一个目标
    currentBox.value = boxes.value.length ? boxes.value[0] : null;
    selectedIndex.value = boxes.value.length ? 0 : -1;
  } catch (err) {
    console.error(err);
    alert("Image detection failed");
  } finally {
    loading.value = false;
  }
};

// 下拉框切换
const onSelectChange = () => {
  if (selectedIndex.value === -1) {
    currentBox.value = boxes.value[0] || null;
  } else {
    currentBox.value = boxes.value[selectedIndex.value];
  }
};

// 点击图片选择最近目标
const onImageClick = (event) => {
  if (!boxes.value.length) return;

  const img = imgRef.value;
  const rect = img.getBoundingClientRect();

  const clickX =
    ((event.clientX - rect.left) / rect.width) * img.naturalWidth;
  const clickY =
    ((event.clientY - rect.top) / rect.height) * img.naturalHeight;

  let minDist = Infinity;
  let closestIndex = 0;

  boxes.value.forEach((box, index) => {
    const cx = (box.xmin + box.xmax) / 2;
    const cy = (box.ymin + box.ymax) / 2;
    const dist = Math.hypot(cx - clickX, cy - clickY);

    if (dist < minDist) {
      minDist = dist;
      closestIndex = index;
    }
  });

  selectedIndex.value = closestIndex;
  currentBox.value = boxes.value[closestIndex];
};
</script>

<style scoped>
.card {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(22, 119, 255, 0.1);
  text-align: center;
}

h2 {
  color: #1677ff;
}

button {
  margin-top: 15px;
  padding: 10px 26px;
  border: none;
  border-radius: 24px;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  color: white;
  font-size: 15px;
  cursor: pointer;
}

.loading {
  margin-top: 10px;
  color: #888;
}

.result img {
  margin-top: 20px;
  max-width: 100%;
  cursor: crosshair;
  border-radius: 12px;
  border: 1px solid #e6f0ff;
}

.selector {
  margin-top: 12px;
}

.coords {
  margin-top: 16px;
  padding: 12px;
  border-radius: 10px;
  background: #f5f9ff;
  border: 1px solid #e6f0ff;
  text-align: left;
}

.coords h4 {
  color: #1677ff;
  margin-bottom: 8px;
}

.coords.empty {
  text-align: center;
  color: #999;
}
</style>
