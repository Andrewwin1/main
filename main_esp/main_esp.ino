
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#define LEDSTATUS 2  // для D1 MINI

const char* ssid = "4G-CPE-BE14";
const char* password = "12345678";
const char* mqtt_server = "192.168.2.140";

WiFiClient espClient;
PubSubClient client(espClient);
unsigned long lastMsg = 0;
#define MSG_BUFFER_SIZE (50)
char msg[MSG_BUFFER_SIZE];
int value = 0;
uint8_t long timer_alive = 0;

// Имя загадки — менять для каждого устройства
const char* device_name = "<>";
const char* mqttTopicIN = "home/<>";      // входящие команды с сервера
const char* mqttTopicOUT = "puzzle/<>";   // исходящие данные с Uno
const char* check_alive_topic = "/home/alive";

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  int i = 0;
  while (WiFi.status() != WL_CONNECTED) {
    i++;
    delay(100);
    if (i >= 50) {
      ESP.restart();
    }
  }
  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LEDSTATUS, HIGH);
  } else {
    ESP.restart();
  }
  randomSeed(micros());
}

void callback(char* topic, byte* payload, unsigned int length) {
  String _payload;
  for (unsigned int i = 0; i < length; i++) {
    _payload += String((char)payload[i]);
  }
  _payload.toLowerCase();
  _payload.trim();

  String _topic(topic);

  // Команды с сервера пересылаем на Uno по UART
  if (_topic.equals(mqttTopicIN) && _payload.length() > 0) {
    Serial.println(_payload);
  }
}

void reconnect() {
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  int i = 0;
  while (!client.connected()) {
    i++;
    String clientId = "ESP8266_";
    clientId += String(random(0xffff), HEX);
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      client.publish(check_alive_topic, device_name);
      client.subscribe(mqttTopicIN);
    } else {
      delay(500);
    }
    if (i >= 20) {
      return;
    }
  }
}

void setup() {
  pinMode(LEDSTATUS, OUTPUT);
  Serial.begin(115200);
  setup_wifi();
  Serial.println();
  delay(1000);
}

bool flag = true;

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LEDSTATUS, LOW);
    setup_wifi();
  } else {
    digitalWrite(LEDSTATUS, HIGH);
  }

  if (client.connected()) {
    client.loop();
  } else {
    reconnect();
  }

  // Читаем данные от Uno и отправляем в MQTT
  if (Serial.available()) {
    String buff = Serial.readStringUntil('\n');
    buff.trim();
    if (buff.length() > 0) {
      char charsbuff[buff.length() + 1];
      buff.toCharArray(charsbuff, buff.length() + 1);
      client.publish(mqttTopicOUT, charsbuff);
    }
  }

  unsigned long now = millis();
  if (now - lastMsg > 2000) {
    lastMsg = now;
  }
  if (timer_alive + 5000 < millis()){
    timer_alive = millis();
    client.publish(check_alive_topic, device_name);
  }
  if (flag){
    client.publish(check_alive_topic, device_name);
    flag = !flag;
  }
}
