
int pins [8] = {2, 3, 4, 5, 6, 7, 8, 9};

void setup() {
  Serial.begin(115200);
  while(!Serial);
  for (int i = 0; i < 8; i++){
    pinMode(pins[i], INPUT_PULLUP);
  }
  pinMode(12, OUTPUT);
  digitalWrite(12, HIGH);

}
int right_way [8] = {0, 1, 0, 0, 0, 1, 0, 1};
int way [8] =       {0, 0, 0, 0, 0, 0, 0, 0};

void loop() {
  for (int i = 0; i < 8; i++){
    way[i] = read_butt(pins[i]);
    delay(10);
  }
  int count = 0;
  for (int i = 0; i < 8; i++){
    if (way[i] == right_way[i]) count ++;
  }
  if (count == 8) {
    digitalWrite(12, LOW);
    delay(1000);
    digitalWrite(12, HIGH);
  }
  Serial.println(count);

}

bool read_butt(int pin){
  int count = 0;
  for (int i = 0; i < 50; i++){
    count += !digitalRead(pin);
  }
  if (count > 40) return true;
  return false;
}
