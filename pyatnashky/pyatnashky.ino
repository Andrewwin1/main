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
}
int game_step = 0;
int last = 0;
int now = 0;
long delay_millis = 0;
void loop() {
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
    now = 0;
    last = 0;
    game_step = 0;
    delay_millis = millis();
    digitalWrite(12, HIGH);
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
