#include <Wire.h>
#include <Adafruit_PCF8575.h>
// адреса 20 и 27

Adafruit_PCF8575 pcf_led;
Adafruit_PCF8575 pcf_butt;

void setup() {
  Serial.begin(115200);
  while (!Serial);

  if (!pcf_led.begin(0x20, &Wire)) {
    Serial.println("Couldn't find PCF8575 led");
    while (1);
  }
  if (!pcf_butt.begin(0x27, &Wire)) {
    Serial.println("Couldn't find PCF8575 butt");
    while (1);
  }
  for (int i = 0; i < 16; i++) {
    pcf_led.pinMode(i, OUTPUT);
    pcf_butt.pinMode(i, INPUT_PULLUP);
  }
  pinMode(12, OUTPUT);
  digitalWrite(12, HIGH);
  randomSeed(analogRead(A0));
  // Отправляем начальное состояние
  Serial.println("STATE:ACTIVE");
}
const char* puzzle_name = "pyatnashky";

// Состояния: 0 = active, 1 = completed
byte puzzle_state = 0;

int game_step = 0;
int last = 0;
int now = 0;
long delay_millis = 0;
bool solved = false;

void loop() {
  // Читаем команды от ESP
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "SET_STATE:ACTIVE") {
      puzzle_state = 0;
      solved = false;
      game_step = 0;
      now = 0;
      last = 0;
      for (int i = 0; i < 16; i++) pcf_led.digitalWrite(i, LOW);
      Serial.println("STATE:ACTIVE");
    } else if (cmd == "SET_STATE:COMPLETED") {
      puzzle_state = 1;
      Serial.println("STATE:COMPLETED");
    }
  }

  // Работаем только если загадка активна
  if (puzzle_state == 1) {
    delay(100);
    return;
  }

  int rand = 0;
  if (!last && !now) {
    rand = random(0, 16);
    now = rand;
    pcf_led.digitalWrite(rand, HIGH);
    delay_millis = millis();
  }
  if (now && !pcf_butt.digitalRead(now)) {
    while (true) {
      rand = random(0, 16);
      if (now != rand) {
        pcf_led.digitalWrite(now, LOW);
        pcf_led.digitalWrite(rand, HIGH);
        last = now;
        now = rand;
        game_step ++;
        delay_millis = millis();
        break;
      }
    }
  }
  if (game_step > 10) {
    for (int i = 0; i < 16; i++) {
      pcf_led.digitalWrite(i, HIGH);
      delay(150);
    }
    digitalWrite(12, LOW);
    delay(5000);
    for (int i = 0; i < 16; i++){
      pcf_led.digitalWrite(i, LOW);
    }
    solved = true;
    puzzle_state = 1;
    now = 0;
    last = 0;
    game_step = 0;
    delay_millis = millis();
    digitalWrite(12, HIGH);
    Serial.println("UNLOCKED");
    Serial.println("STATE:COMPLETED");
  }
  if (delay_millis + 1200 < millis()){
    delay_millis = millis();
    for (int i = 0; i < 16; i++){
      pcf_led.digitalWrite(i, LOW);
    }
    now = 0;
    last = 0;
    game_step = 0;
  }
}
