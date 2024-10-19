import cv2
from PIL import Image
import threading

class Camera:
    def __init__(self):
        self.camera = None
        self.lock = threading.Lock()
        self.is_running = False

    def start(self):
        with self.lock:
            if self.camera is None:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    print("Error: Could not open camera")
                    return False
            self.is_running = True
        return True

    def stop(self):
        with self.lock:
            self.is_running = False
            if self.camera:
                self.camera.release()
                self.camera = None

    def capture_image(self):
        with self.lock:
            if not self.is_running or self.camera is None:
                return None
            ret, frame = self.camera.read()
            if ret:
                return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            else:
                print("Error: Could not capture frame with OpenCV")
                return None

    def isOpened(self):
        with self.lock:
            return self.camera is not None and self.camera.isOpened() and self.is_running

def get_camera():
    return Camera()

if __name__ == "__main__":
    camera = get_camera()
    image = camera.capture_image()
    
    if image is not None:
        image.save('test_image.jpg')
        print("Image captured successfully")
        
        # Show the image
        image.show()
    else:
        print("Couldn't capture image")
    
    camera.stop()
