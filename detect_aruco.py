import cv2
import requests

ESP32_IP = "192.168.8.30"

def send_wifi_command(cmd_id):
    url = f"http://{ESP32_IP}/cmd?val={cmd_id}"
    try:
        response = requests.get(url, timeout=0.3)
        if response.status_code == 200:
            print(f"[WIFI SUCCESS] -> Command {cmd_id} terkirim ke ESP32!")
    except Exception as e:
        print(f"[WIFI ERROR] Gagal konek ke ESP32 ({e})")

cap = cv2.VideoCapture(2)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

last_command = None

print("Sistem ArUco Wi-Fi Siap! Arahkan marker ke kamera iPhone.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil feed dari kamera iPhone.")
        break

    corners, ids, rejected = detector.detectMarkers(frame)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for marker_id in ids.flatten():
            if 0 <= marker_id <= 3:
                if marker_id != last_command:
                    send_wifi_command(marker_id)
                    last_command = marker_id

    cv2.imshow("Kamera ArUco Wi-Fi Robot", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()