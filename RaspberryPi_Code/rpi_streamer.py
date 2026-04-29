import cv2
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver
import time


class StreamingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/stream":
            self.send_response(200)
            self.send_header("Age", 0)
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.send_header(
                "Content-Type", "multipart/x-mixed-replace; boundary=FRAME"
            )
            self.end_headers()
            try:
                while True:
                    rc, img = cap.read()
                    if not rc:
                        time.sleep(0.1)
                        continue
                    # Asegurar buen FPS y comprimir MJPEG a calidad 60 para red local rapida
                    val, frame = cv2.imencode(
                        ".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60]
                    )
                    self.wfile.write(b"--FRAME\r\n")
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", len(frame))
                    self.end_headers()
                    self.wfile.write(frame.tobytes())
                    self.wfile.write(b"\r\n")
            except Exception:
                pass
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


cap = cv2.VideoCapture(0)
# Reducimos resolución para maximizar los FPS sobre red (640x480 es perfecto para template matching)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)

print("[STREAMER] Iniciando transmision inalambrica en puerto 5000...")
server = StreamingServer(("", 5000), StreamingHandler)

try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    print("\n[STREAMER] Apagando transmision de camara...")
    cap.release()
    server.server_close()
