import cv2
import numpy as np
import time
from ultralytics import YOLO


class YOLOService:
    def __init__(self, model_path: str):
        self.model = YOLO(model_path, task="detect")
        # 预热模型
        self.model(np.zeros((48, 48, 3), dtype=np.uint8))

    def detect_image(self, img_bgr, conf: float = 0.25):
        """
        返回结构说明：
        {
            "image": np.ndarray,          # 画好框的图像
            "boxes": [                    # 结构化检测框
                {
                    "xmin": int,
                    "ymin": int,
                    "xmax": int,
                    "ymax": int,
                    "cls_id": int,
                    "cls_name": str,
                    "conf": float
                }
            ],
            "time": float
        }
        """

        t1 = time.time()
        results = self.model.predict(img_bgr, conf=conf)[0]
        t2 = time.time()

        annotated_img = results.plot()

        boxes = []
        names = results.names

        if results.boxes is not None and len(results.boxes) > 0:
            xyxy = results.boxes.xyxy.cpu().numpy()
            cls_ids = results.boxes.cls.cpu().numpy()
            confs = results.boxes.conf.cpu().numpy()

            for i in range(len(xyxy)):
                xmin, ymin, xmax, ymax = map(int, xyxy[i])
                cls_id = int(cls_ids[i])
                boxes.append({
                    "xmin": xmin,
                    "ymin": ymin,
                    "xmax": xmax,
                    "ymax": ymax,
                    "cls_id": cls_id,
                    "cls_name": names[cls_id],
                    "conf": round(float(confs[i]), 4)
                })

        return {
            "image": annotated_img,
            "boxes": boxes,
            "time": round(t2 - t1, 3)
        }
