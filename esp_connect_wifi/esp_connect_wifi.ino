#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

const char* ssid = "iPad";
const char* password = "pacarkakjosh";

WebServer server(80);
Servo gripperServo;

// PIN DRIVER MX1508 
const int IN1 = 16;
const int IN2 = 17;
const int IN3 = 18;
const int IN4 = 19;

// PIN SERVO SG90 (P1)
const int SERVO_PIN = 2;

// Derajat Gerakan Servo
const int ANGLE_BUKA = 10;   // sudut buat gripper terbuka
const int ANGLE_JEPIT = 90;  // sudut buat gripper menjepit

// FUNGSI KONTROL MOTOR MX1508
void robotMaju() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void robotBelokKiri() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH); // kiri mundur
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);  // kanan maju
}

void robotBelokKanan() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);  // kiri maju
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH); // kanan mundur
}

void robotPutarBalik() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void robotStop() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

// FUNGSI GRIPPER 
void jepitBenda() {
  robotStop();
  gripperServo.write(ANGLE_JEPIT);
  delay(500);
}

void lepasBenda() {
  robotStop();
  gripperServo.write(ANGLE_BUKA);
  delay(500);
}

void handleCommand() {
  if (server.hasArg("val")) {
    String command = server.arg("val");
    
    if (command == "0") {
      robotMaju();
      Serial.println(">>> [ROBOT] MAJU");
    } 
    else if (command == "1") {
      robotBelokKiri();
      Serial.println(">>> [ROBOT] BELOK KIRI");
    } 
    else if (command == "2") {
      robotBelokKanan();
      Serial.println(">>> [ROBOT] BELOK KANAN");
    } 
    else if (command == "3") {
      robotPutarBalik();
      Serial.println(">>> [ROBOT] PUTAR BALIK");
    }
    // command tambahan klo butuh trigger jepit/buka via Wi-Fi
    else if (command == "GRAB") {
      jepitBenda();
      Serial.println(">>> [GRIPPER] MENJEPIT");
    }
    else if (command == "RELEASE") {
      lepasBenda();
      Serial.println(">>> [GRIPPER] MELEPAS");
    }

    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Bad Request");
  }
}

void setup() {
  Serial.begin(115200);

  // setup Pin Motor Driver
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  // setup Servo
  gripperServo.attach(SERVO_PIN);
  gripperServo.write(ANGLE_BUKA); // Posisi awal terbuka

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
}

void loop() {
  server.handleClient();
}