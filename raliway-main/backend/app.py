import os
import cv2
import uuid
import json
import shutil
import subprocess
import numpy as np
from fastapi import FastAPI, UploadFile, File, WebSocket
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect

from .yolo_service import YOLOService

app = FastAPI()

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "../railway_obstacles_detection/runs/detect/train/weights/best.pt"
OUTPUT_DIR = "outputs/images"
VIDEO_OUTPUT_DIR = "outputs/videos"
VIDEO_JSON_DIR = "outputs/video_json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)
os.makedirs(VIDEO_JSON_DIR, exist_ok=True)

yolo = YOLOService(MODEL_PATH)


@app.get("/ping123")
async def ping():
    return {"msg": "ok"}


# ===============================
# HTTP 图片检测
# ===============================
@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    contents = await file.read()
    np_img = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    result = yolo.detect_image(img)

    filename = f"{uuid.uuid4().hex}.jpg"
    save_path = os.path.join(OUTPUT_DIR, filename)
    cv2.imwrite(save_path, result["image"])

    boxes = result.get("boxes", [])
    first_box = boxes[0] if boxes else None

    return {
        "image_url": f"/result/image/{filename}",
        "total": len(boxes),
        "first_box": first_box,
        "boxes": boxes
    }


@app.get("/result/image/{name}")
def get_image(name: str):
    return FileResponse(os.path.join(OUTPUT_DIR, name))


# ===============================
# WebSocket 实时检测（保持不变）
# ===============================
@app.websocket("/ws/detect")
async def ws_detect(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connected")

    try:
        while True:
            data = await websocket.receive_bytes()

            np_img = np.frombuffer(data, np.uint8)
            img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if img is None:
                continue

            result = yolo.detect_image(img)
            boxes = result.get("boxes", [])

            await websocket.send_json({
                "total": len(boxes),
                "boxes": boxes,
                "first_box": boxes[0] if boxes else None
            })

            ok, encoded = cv2.imencode(".jpg", result["image"])
            if ok:
                await websocket.send_bytes(encoded.tobytes())

    except WebSocketDisconnect:
        print("WebSocket disconnected (normal)")
    except Exception as e:
        print("WebSocket error:", e)
    finally:
        print("WebSocket handler finished")


# ===============================
# ✅ 视频检测（Plan B 增强版）
# ===============================
@app.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1]
    input_video_path = os.path.join(
        VIDEO_OUTPUT_DIR,
        f"{uuid.uuid4().hex}_input{suffix}"
    )

    with open(input_video_path, "wb") as f:
        f.write(await file.read())

    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        return JSONResponse({"error": "Cannot open video"}, status_code=400)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    output_filename = f"{uuid.uuid4().hex}_result.mp4"
    output_video_path = os.path.join(VIDEO_OUTPUT_DIR, output_filename)
    # OpenCV 内置 ffmpeg 不含 x264：先用 mp4v 写中间文件，
    # 全部帧写完后再用系统 ffmpeg 转码为浏览器可播放的 H.264
    raw_video_path = output_video_path.replace(".mp4", "_raw.mp4")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        raw_video_path, fourcc, fps if fps and fps > 0 else 25.0, (width, height)
    )
    if not out.isOpened():
        cap.release()
        return JSONResponse({"error": "Cannot create video writer"}, status_code=500)

    # ✅ Plan B：检测结果收集
    objects = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result = yolo.detect_image(frame)
        out.write(result["image"])

        boxes = result.get("boxes", [])
        for b in boxes:
            objects.append({
                "frame": frame_idx,
                "time": frame_idx / fps if fps > 0 else 0,
                "cls_name": b.get("cls_name"),
                "conf": b.get("conf"),
                "xmin": b.get("xmin"),
                "ymin": b.get("ymin"),
                "xmax": b.get("xmax"),
                "ymax": b.get("ymax"),
            })

        frame_idx += 1

    cap.release()
    out.release()

    # 转码为 H.264（Chrome/Firefox/Edge 均可直接播放）；
    # 若容器内没有 ffmpeg 则回退使用 mp4v 原始文件
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin and os.path.exists(raw_video_path):
        try:
            subprocess.run(
                [
                    ffmpeg_bin, "-y", "-i", raw_video_path,
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
                    output_video_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.remove(raw_video_path)
        except Exception as e:
            print("ffmpeg transcode failed, fallback to raw:", e)
            if os.path.exists(output_video_path):
                os.remove(output_video_path)
            os.replace(raw_video_path, output_video_path)
    else:
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        os.replace(raw_video_path, output_video_path)

    # 保存 JSON（可选，但强烈推荐）
    json_filename = f"{uuid.uuid4().hex}.json"
    json_path = os.path.join(VIDEO_JSON_DIR, json_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "meta": {
                "fps": fps,
                "total_frames": frame_idx,
                "width": width,
                "height": height,
            },
            "objects": objects
        }, f, ensure_ascii=False, indent=2)

    return {
        "video_url": f"/result/video/{output_filename}",
        "json_url": f"/result/video_json/{json_filename}",
        "meta": {
            "fps": fps,
            "total_frames": frame_idx,
            "width": width,
            "height": height,
        },
        "objects": objects
    }


# ===============================
# 视频结果
# ===============================
@app.api_route("/result/video/{name}", methods=["GET", "HEAD"])
def get_video(name: str):
    path = os.path.join(VIDEO_OUTPUT_DIR, name)

    def iterfile():
        with open(path, "rb") as f:
            yield from f

    return StreamingResponse(iterfile(), media_type="video/mp4")


# ===============================
# 视频 JSON 结果
# ===============================
@app.get("/result/video_json/{name}")
def get_video_json(name: str):
    return FileResponse(os.path.join(VIDEO_JSON_DIR, name))
