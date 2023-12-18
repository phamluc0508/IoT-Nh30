#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <uri/UriBraces.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHTPIN 23  // Chân kết nối Out của DHT22
#define DHTTYPE DHT22  
#define WIFI_SSID "AB24"
#define WIFI_PASSWORD "LLPPKKAA"
// Defining the WiFi channel speeds up the connection:
#define WIFI_CHANNEL 6

WebServer server(80);
DHT dht(DHTPIN, DHTTYPE);

void handleJsonRequest() {
  float temperature=dht.readTemperature(),humidity=dht.readHumidity(),spo=15,heartbeat=8;
  Serial.print("Humidity: ");
  Serial.print(humidity);
  Serial.print("%, Temperature: ");
  Serial.print(temperature);
  Serial.println("°C");
  String serverUrl = "http://192.168.1.4:5000/checkstatus?temperature="+String(temperature)+"&humidity="+String(humidity)+"&spo="+String(spo)+"&heartbeat="+String(heartbeat);
  HTTPClient http;
  http.begin(serverUrl.c_str());
  int httpCode = http.GET();

  // Xử lý response JSON
  
    String payload = http.getString();
    Serial.println("Response JSON:");
    Serial.println(payload);
    // loại bỏ [] trong json trả về
    

    // Phân tích chuỗi JSON
    DynamicJsonDocument jsonDoc(1024); // Kích thước đệm cho JSON
    DeserializationError error = deserializeJson(jsonDoc, payload);

    // Kiểm tra lỗi khi phân tích JSON
    const char* disease = jsonDoc["message"];

  http.end();
  // Tạo một đối tượng JSON
  StaticJsonDocument<200> jsonDocument;
  
  // Thêm dữ liệu vào JSON
  jsonDocument["disease"] = disease;
  jsonDocument["heartbeat"] = heartbeat;
  jsonDocument["humidity"] = humidity;
  jsonDocument["spo"] = spo;
  jsonDocument["temperature"] = temperature;
  // Chuyển đối tượng JSON thành chuỗi JSON
  String jsonString;
  serializeJson(jsonDocument, jsonString);

  // Gửi chuỗi JSON về client
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "application/json", jsonString);

}
void setup(void) {
  Serial.begin(115200);
 

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, WIFI_CHANNEL);
  Serial.print("Connecting to WiFi ");
  Serial.print(WIFI_SSID);
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(100);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  //server.on("/", sendHtml);

  server.on("/kiemTraTinhTrang", HTTP_GET, handleJsonRequest);

  server.begin();
  Serial.println("HTTP server started");
}

void loop(void) {
  server.handleClient();
  delay(2);
}
