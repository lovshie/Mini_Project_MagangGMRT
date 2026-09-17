#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "iPad";
const char* password = "pacarkakjosh";

WebServer server(80);

// pin driver motor MX1508
const int IN1 = 16;
const int IN2 = 17;
const int IN3 = 18;
const int IN4 = 19;

// timer failsafe (buat ngecek koneksi putus)
unsigned long lastCommandTime = 0;
const unsigned long TIMEOUT_MS = 1500; // klo 1.5 detik ga ada data dari Python jadi berhenti

void robotMaju() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void robotBelokKanan() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);  // kiri maju
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH); // kanan mundur
}

void robotBelokKiri() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH); // kiri mundur
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);  // kanan maju
}

void robotStop() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void handleCommand() {
  if (server.hasArg("val")) {
    String command = server.arg("val");
    lastCommandTime = millis(); // reset timer tiap kali perintah masuk
    
    // command marker aruco
    if (command == "0") {
      robotMaju();
      Serial.println(">>> [ROBOT] 0: MAJU LURUS");
    } 
    else if (command == "1") {
      robotBelokKanan();
      Serial.println(">>> [ROBOT] 1: BELOK KANAN");
    } 
    else if (command == "2") {
      robotBelokKiri();
      Serial.println(">>> [ROBOT] 2: BELOK KIRI");
    } 
    else if (command == "3") {
      robotStop();
      Serial.println(">>> [ROBOT] 3: BERHENTI / STOP");
    }

    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Bad Request");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  robotStop(); 

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address ESP32: ");
  Serial.println(WiFi.localIP());

  server.on("/cmd", handleCommand);
  server.begin();
  
  lastCommandTime = millis();
}

void loop() {
  server.handleClient();

  // klo wifi atau python diem lebih dari 1.5 detik, matiin pin motor langsung ke 0 (LOW)
  if (millis() - lastCommandTime > TIMEOUT_MS) {
    robotStop();
  }
}