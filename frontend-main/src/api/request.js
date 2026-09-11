import axios from "axios";

const request = axios.create({
  // 本地开发默认走 /api（由 Vite/Nginx 代理到后端）；
  // 也可在构建时通过 VITE_API_BASE 环境变量覆盖
  baseURL: import.meta.env.VITE_API_BASE || "/api",
  timeout: 300000, // 视频检测耗时较长，超时放宽到 5 分钟
});

export default request;
