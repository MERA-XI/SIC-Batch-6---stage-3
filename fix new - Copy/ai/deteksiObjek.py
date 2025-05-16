import os
from yolov5 import YOLOv5

class ObjectDetector:
    def __init__(self):
        # model_path = os.path.join("model", "yolov5n.pt")
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "model", "yolov5n.pt")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model YOLOv5 not found at {model_path}")
        self.model = YOLOv5(model_path, device='cpu')
    
    def detect(self, img_data):
        results = self.model.predict(img_data)
        objects = [f"{results.names[int(cls)]} ({float(conf):.2f})" 
                  for *_, conf, cls in results.pred[0]]
        return objects, results