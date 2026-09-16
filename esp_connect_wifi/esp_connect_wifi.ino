#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "Tselhome-3697";
const char* password = "63791966";

WebServer server(80);
const int LED_PIN = 2; 

void handleCommand() {
  if (server.hasArg("val")) {
    String command = server.arg("val");
    
    if (command == "0") {
      digitalWrite(LED_PIN, LOW);
      Serial.println(">>> Wi-Fi Command 0: MAJU / STOP");
    } 
    else if (command == "1") {
      digitalWrite(LED_PIN, HIGH);
      Serial.println(">>> Wi-Fi Command 1: BELOK KIRI");
    } 
    else if (command == "2") {
      Serial.println(">>> Wi-Fi Command 2: BELOK KANAN");
    } 
    else if (command == "3") {
      Serial.println(">>> Wi-Fi Command 3: PUTAR BALIK");
    }

    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Bad Request");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi Connected!");
  Serial.print("IP Address ESP32: ");
  Serial.println(WiFi.localIP());

  server.on("/cmd", handleCommand);
  server.begin();
}

void loop() {
  server.handleClient();
}