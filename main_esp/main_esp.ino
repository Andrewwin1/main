
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
const char* mqttTopicIN = "home/";
const char* check_alive_topic = "/home/alive";
const char* device_name = "<>"; // сюда вставить имя устройства
const char* test = "1"; // сюда вставить имя устройства

void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  int i = 0;
  while (WiFi.status() != WL_CONNECTED) {
    i++;
    delay(100);
    //Serial.print(".");
    if (i >= 5) {
      //Serial.println("error conection");
      return;
    }
  }
  if (WiFi.status() == WL_CONNECTED) {
    digitalWrite(LEDSTATUS, HIGH);
  }
  else ESP.restart();
  randomSeed(micros());
  /*
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
*/
}


void callback(char* topic, byte* payload, unsigned int length) {
  String _payload;
  int a = 0;
  for (unsigned int i = 0; i < length; i++) {
    _payload += String((char)payload[i]);
  };
  _payload.toLowerCase();
  _payload.trim();

 
  
  // Сравниваем с топиками

  String _topic(topic);
  if (_topic.equals(mqttTopicIN)) {
    char charsbuff[_payload.length()+1];
    _payload.toCharArray(charsbuff, _payload.length()+1);
    String str = String(charsbuff);
    Serial.print(str);
  }
 
}


void reconnect() {
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  // Loop until we're reconnected
  int i = 0;
  while (!client.connected()) {
    i++;
    //Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client_western_chair";
    //clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str())) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish(check_alive_topic, device_name);
      // ... and resubscribe
      client.subscribe(mqttTopicIN);
      
    } else {
      //Serial.print("failed, rc=");
      //Serial.print(client.state());
      //Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(500);
    }
    if (i >= 20) {
      //Serial.println("error conection");
      return;
    }
  }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(LEDSTATUS, OUTPUT);  // Initialize the BUILTIN_LED pin as an output
  Serial.begin(115200);
  //Serial.swap();  
  setup_wifi();
  Serial.println()
  delay(1000);
}

bool flag = true;

void loop() {

  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(LEDSTATUS, LOW);  // 14 для еспшки на борту уно
    setup_wifi();
  }else digitalWrite(LEDSTATUS, HIGH);

  if (client.connected()) {
    client.loop();
  } else {
    reconnect();
  }
  if (Serial.available()) {
    String buff = Serial.readString();
    char charsbuff[buff.length()+1];
    buff.toCharArray(charsbuff, buff.length()+1);
    client.publish("top_in_server", charsbuff );
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
    client.publish(check_alive_topic, test);  
    flag = !flag;
  }


  // here you can write your code

  
}
