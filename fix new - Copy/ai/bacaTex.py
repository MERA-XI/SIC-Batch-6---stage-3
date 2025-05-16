import easyocr
import cv2
import numpy as np
import time

class TextReader:
    def __init__(self, language='en+id', min_confidence=0.5):
        self.language = language
        self.min_confidence = min_confidence
        self.reader = easyocr.Reader(language.split('+'))
        self.last_results = []
        self.processing_fps = 0
    
    def read(self, frame):
        results, processed_img = self._detect_text(frame)
        texts = [text for (_, text, _) in results]
        return " ".join(texts) if texts else "Tidak ada teks terdeteksi", processed_img
    
    def _detect_text(self, frame):
        start_time = time.time()
        processed = self._preprocess(frame)
        
        try:
            results = self.reader.readtext(processed)
            filtered_results = [(box, text, conf) for (box, text, conf) in results 
                              if conf > self.min_confidence]
            
            self.processing_fps = 1.0 / (time.time() - start_time)
            self.last_results = filtered_results
            
            result_frame = self._draw_results(frame.copy())
            return filtered_results, result_frame
            
        except Exception as e:
            print(f"OCR Error: {e}")
            return [], frame
    
    def _preprocess(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        return sharpened
    
    def _draw_results(self, frame):
        for (box, text, conf) in self.last_results:
            box = np.array(box, dtype=np.int32)
            cv2.polylines(frame, [box], True, (0, 255, 0), 2)
            (x, y) = (box[0][0], box[0][1])
            (w, h) = (box[2][0] - box[0][0], box[2][1] - box[0][1])
            
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y - 30), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
            
            cv2.putText(frame, f"{text} ({conf:.2f})", (x, y - 10),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return frame