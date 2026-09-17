import cv2
import requests
import math
import time
import threading

ESP32_IP = "192.168.8.200"

MARKER_SIZE_CM = 10.0   # ukuran aruconya 10cm
FOCAL_LENGTH = 1950.0   # estimasi jarak aruco sm kamera
TARGET_DISTANCE_CM = 30.0  # batas jarak robot buat eksekusi perintah marker

last_send_time = 0
SEND_INTERVAL = 0.4  # ngirim perintah minimal ada jeda 0.4 detik

def _wifi_worker(cmd_id):
    url = f"http://{ESP32_IP}/cmd?val={cmd_id}"
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            print(f"[WIFI SUCCESS] -> Yeayy command {cmd_id} berhasil terkirim ke ESP32!")
    except Exception as e:
        print(f"[WIFI ERROR] Gagal connect ke ESP32 nya bro, koneksi putus! ({e})")

def send_wifi_command(cmd_id):
    global last_send_time
    current_time = time.time()
    
    if current_time - last_send_time >= SEND_INTERVAL:
        last_send_time = current_time
        threading.Thread(target=_wifi_worker, args=(cmd_id,), daemon=True).start()

def execute_marker_action(marker_id):
    # logika robotnya
    if marker_id == 0:
        print("-> Ketemu nih aruco 0: MAJUUU")
        send_wifi_command(0)  # 0 = maju

    elif marker_id == 1:
        print("-> Ketemu nih aruco 1 LETS GOO BELOK KANAN")
        send_wifi_command(1)  # 1 = Belok Kanan

    elif marker_id == 2:
        print("-> Ketemu nih aruco 2 CUSSS BELOK KIRI")
        send_wifi_command(2)  # 2 = Belok Kiri

    elif marker_id == 3:
        print("-> Ketemu nih aruco 3 STOOPPP")
        send_wifi_command(3)  # 3 = Stop

# ini buat kamera iphone, kalo mau pake webcam biasa ganti 2 jadi 0
cap = cv2.VideoCapture(2)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

last_executed_marker = None

print("Sistem ArUco Direct Control Siap!")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil feed kamera.")
        send_wifi_command(3) # kalo kamera mati, auto stop
        break

    height, width, _ = frame.shape
    frame_center_x = width // 2

    corners, ids, rejected = detector.detectMarkers(frame)

    # garis pandu kuning di tengah layar
    cv2.line(frame, (frame_center_x, 0), (frame_center_x, height), (0, 255, 255), 2)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i, marker_id in enumerate(ids.flatten()):
            if 0 <= marker_id <= 3:
                pts = corners[i][0]

                # hitung titik tengah marker (X, Y)
                center_x = int((pts[0][0] + pts[1][0] + pts[2][0] + pts[3][0]) / 4)
                center_y = int((pts[0][1] + pts[1][1] + pts[2][1] + pts[3][1]) / 4)

                # hitung lebar piksel & jarak cm
                pixel_width = math.sqrt((pts[1][0] - pts[0][0])**2 + (pts[1][1] - pts[0][1])**2)
                distance_cm = (MARKER_SIZE_CM * FOCAL_LENGTH) / pixel_width if pixel_width > 0 else 0

                # tampilkan info marker di layar kamera
                cv2.circle(frame, (center_x, center_y), 7, (0, 0, 255), -1)
                text_info = f"ID: {marker_id} | Jarak: {distance_cm:.1f}cm"
                cv2.putText(frame, text_info, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

                # klo robot sudah deket sm marker (jarak <= 30cm)
                if distance_cm <= TARGET_DISTANCE_CM:
                    if marker_id != last_executed_marker:
                        print(f"\n[Target Sampai] ArUco ID {marker_id} terdeteksi di jarak {distance_cm:.1f}cm")
                        
                        # eksekusi gerakan sesuai ID marker
                        execute_marker_action(marker_id)
                        
                        last_executed_marker = marker_id

    cv2.imshow("Kamera ArUco Direct Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        send_wifi_command(3) # pencet 'q' auto stop
        break

cap.release()
cv2.destroyAllWindows()