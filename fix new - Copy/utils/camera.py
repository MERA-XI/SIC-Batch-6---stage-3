import requests
import numpy as np
import cv2
import time
import os
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Suppress HTTPS warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Camera:
    def __init__(self):
        self.CAMERA_IP = "192.168.43.96"
        self.BASE_URL = f"http://{self.CAMERA_IP}/capture"
        self.TIMEOUT = 10  # seconds
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1  # second
        self.SAVE_DIR = "captured_images"

        # Create directory for captured images if it doesn't exist
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)

        # Test connection on initialization
        if not self._test_connection():
            raise RuntimeError("Kamera tidak dapat dihubungi")

    def _test_connection(self):
        """Test if camera is reachable"""
        try:
            response = requests.get(f"http://{self.CAMERA_IP}", timeout=5)
            return response.status_code == 200
        except:
            return False

    def capture(self, mode):
        """Capture image with retry mechanism and save it"""
        params = {
            'mode': mode,
            'quality': 80,
            'width': 640,
            'height': 480
        }

        for attempt in range(self.MAX_RETRIES):
            try:
                start_time = time.time()

                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=self.TIMEOUT,
                    verify=False
                )

                if response.status_code != 200:
                    print(f"Attempt {attempt+1}: HTTP {response.status_code}")
                    continue

                if not response.content:
                    print(f"Attempt {attempt+1}: Empty response")
                    continue

                if not response.content.startswith(b'\xff\xd8'):
                    print(f"Attempt {attempt+1}: Invalid image data")
                    continue

                img = cv2.imdecode(
                    np.frombuffer(response.content, dtype=np.uint8),
                    cv2.IMREAD_COLOR
                )

                if img is not None:
                    print(f"Capture successful in {time.time()-start_time:.2f}s")

                    # Save the image
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{mode}_{timestamp}.jpg"
                    filepath = os.path.join(self.SAVE_DIR, filename)
                    cv2.imwrite(filepath, img)
                    print(f"Image saved to: {filepath}")

                    return img

                print(f"Attempt {attempt+1}: Failed to decode image")

            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt+1}: Request failed - {str(e)}")
            except Exception as e:
                print(f"Attempt {attempt+1}: Unexpected error - {str(e)}")

            if attempt < self.MAX_RETRIES - 1:
                time.sleep(self.RETRY_DELAY)

        print("All capture attempts failed")
        return None

    def is_camera_available(self):
        try:
            response = requests.get(f"http://{self.CAMERA_IP}", timeout=3)
            return response.status_code == 200
        except:
            return False