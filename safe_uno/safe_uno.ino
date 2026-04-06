int pins [3] = {2, 4, 5};


void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 3; i++){
    pinMode(i, INPUT_PULLUP);
  }

}

void loop() {
  for (int i = 0; i < 3; i++){
    Serial.print(read_butt(pins[i]));
  }
  Serial.println();

}

bool read_butt(int pin){
  int count = 0;
  for (int i = 0; i < 50; i++){
    count += digitalRead(pin);
    delay(1);
  }
  if (count > 40) return true;
  return false;
}
