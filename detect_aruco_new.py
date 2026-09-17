import cv2
import requests
import math
import time
import threading

ESP32_IP = "172.20.10.4"

MARKER_SIZE_CM = 10.0   # ukuran aruconya 10cm
FOCAL_LENGTH = 1950.0   # estimasi jarak aruco sm kamera
TARGET_DISTANCE_CM = 30.0  # batas garis finish robot sebelum ngerjain tugas utamanya

last_send_time = 0
SEND_INTERVAL = 0.4  # ngirim perintah minimal ada jeda 0.4 detik

def _wifi_worker(cmd_id):
    url = f"http://{ESP32_IP}/cmd?val={cmd_id}"
    try:
        response = requests.get(url, timeout=0.5)
        if response.status_code == 200:
            print(f"[WIFI SUCCESS] -> Yeayy command {cmd_id} berhasil terkirim ke ESP32!")
    except Exception as e:
        print(f"[WIFI ERROR] Gagal connect ke ESP32 nya bro ({e})")

def send_wifi_command(cmd_id):
    global last_send_time
    current_time = time.time()
    
    # klo yang dikirim string "GRAB" / "RELEASE", langsung bypass timer biar gak ketahan
    is_special_cmd = isinstance(cmd_id, str) and cmd_id in ["GRAB", "RELEASE"]
    
    if is_special_cmd or (current_time - last_send_time >= SEND_INTERVAL):
        last_send_time = current_time
        threading.Thread(target=_wifi_worker, args=(cmd_id,), daemon=True).start()

def _execute_mission(marker_id):
    if marker_id == 0:
        print("Misi 1: jepit barang terus belok kanan lurus cari marker 1")
        send_wifi_command("GRAB")     # jepit pake servo
        time.sleep(1.2)
        send_wifi_command(2)          # belok kanan
        time.sleep(1)
        send_wifi_command(0)          # maju lurus

    elif marker_id == 1:
        print("Misi 2: belok kiri terus lurus cari marker 2")
        send_wifi_command(1)          # belok kiri
        time.sleep(1)
        send_wifi_command(0)          # maju lurus

    elif marker_id == 2:
        print("Misi 3: lepas barang terus belok kanan lurus cari marker 3")
        send_wifi_command("RELEASE")  # lepas pake servo
        time.sleep(1.2)
        send_wifi_command(2)          # belok kanan
        time.sleep(1)
        send_wifi_command(0)          # maju lurus

    elif marker_id == 3:
        print("Misi Final: putar balik & kelar bro!")
        send_wifi_command(3)          # putar balik

def run_mission_async(marker_id):
    threading.Thread(target=_execute_mission, args=(marker_id,), daemon=True).start()

# ini buat kamera iphone, kalo mau pake webcam biasa ganti 2 jadi 0
cap = cv2.VideoCapture(2)
dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
parameters = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(dictionary, parameters)

last_executed_marker = None
last_command = None

print("Sistem Full Autonomous Sequence ArUco + Gripper Siap!")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil feed kamera.")
        break

    height, width, _ = frame.shape
    frame_center_x = width // 2

    corners, ids, rejected = detector.detectMarkers(frame)

    # ini buat garis pandu tengah layar (kuning)
    cv2.line(frame, (frame_center_x, 0), (frame_center_x, height), (0, 255, 255), 2)

    if ids is not None:
        cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        for i, marker_id in enumerate(ids.flatten()):
            if 0 <= marker_id <= 3:
                pts = corners[i][0]

                # hitung titik tengah marker (X, Y)
                center_x = int((pts[0][0] + pts[1][0] + pts[2][0] + pts[3][0]) / 4)
                center_y = int((pts[0][1] + pts[1][1] + pts[2][1] + pts[3][1]) / 4)

                # hitung lebar piksel marker sm estimasi jarak cm
                pixel_width = math.sqrt((pts[1][0] - pts[0][0])**2 + (pts[1][1] - pts[0][1])**2)
                distance_cm = (MARKER_SIZE_CM * FOCAL_LENGTH) / pixel_width if pixel_width > 0 else 0

                # buat cek posisi kelurusan (alignment)
                offset_x = center_x - frame_center_x
                
                status_align = "LURUS"
                if offset_x < -40:
                    status_align = "PERLU KIRI"
                elif offset_x > 40:
                    status_align = "PERLU KANAN"

                # tampilkan titik tengah marker dan info ID, jarak, dan status alignment
                cv2.circle(frame, (center_x, center_y), 7, (0, 0, 255), -1)
                text_info = f"ID: {marker_id} | Jarak: {distance_cm:.1f}cm | {status_align}"
                
                # ukuran tulisan tampilan di layar
                cv2.putText(frame, text_info, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

                # ini buat logika navigasi robot 
                if distance_cm > TARGET_DISTANCE_CM:
                    # ini buat ngecek status align dan ngirim command ke ESP32 kalo robot perlu belok kiri/kanan atau maju lurus
                    if status_align == "PERLU KIRI":
                        if last_command != "ALIGN_KIRI":
                            print(f"-> Ngelurusin KIRI (Jarak: {distance_cm:.1f}cm)")
                            last_command = "ALIGN_KIRI"
                        send_wifi_command(1)  # Belok Kiri

                    elif status_align == "PERLU KANAN":
                        if last_command != "ALIGN_KANAN":
                            print(f"-> Ngelurusin KANAN (Jarak: {distance_cm:.1f}cm)")
                            last_command = "ALIGN_KANAN"
                        send_wifi_command(2)  # Belok Kanan

                    elif status_align == "LURUS":
                        if last_command != "MENDEKAT":
                            print(f"-> Posisi lurus, MENDEKAT (Jarak: {distance_cm:.1f}cm)")
                            last_command = "MENDEKAT"
                        send_wifi_command(0)  # Maju

                else:
                    # robot udah di jarak ideal
                    if marker_id != last_executed_marker:
                        print(f"\n[Target Sampai] ArUco ID {marker_id} dapet di jarak {distance_cm:.1f}cm")
                        
                        run_mission_async(marker_id)

                        print()  # cuma enter spasi biar rapih
                        last_executed_marker = marker_id
                        last_command = f"DONE_{marker_id}"

    cv2.imshow("Kamera ArUco Autonomous Robot", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()