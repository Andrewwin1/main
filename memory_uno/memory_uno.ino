
int pins [8] = {2, 3, 4, 5, 6, 7, 8, 9};
const char* puzzle_name = "memory";

// Состояния: 0 = active, 1 = completed
byte puzzle_state = 0;

void setup() {
  Serial.begin(115200);
  while(!Serial);
  for (int i = 0; i < 8; i++){
    pinMode(pins[i], INPUT_PULLUP);
  }
  pinMode(12, OUTPUT);
  digitalWrite(12, HIGH);
  // Отправляем начальное состояние
  Serial.println("STATE:ACTIVE");
}
int right_way [8] = {0, 1, 0, 0, 0, 1, 0, 1};
int way [8] =       {0, 0, 0, 0, 0, 0, 0, 0};
bool solved = false;

void loop() {
  // Читаем команды от ESP
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "SET_STATE:ACTIVE") {
      puzzle_state = 0;
      solved = false;
      digitalWrite(12, HIGH);
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

  for (int i = 0; i < 8; i++){
    way[i] = read_butt(pins[i]);
    delay(10);
  }
  int count = 0;
  for (int i = 0; i < 8; i++){
    if (way[i] == right_way[i]) count ++;
  }
  if (count == 8 && !solved) {
    solved = true;
    puzzle_state = 1;
    digitalWrite(12, LOW);
    delay(1000);
    digitalWrite(12, HIGH);
    Serial.println("UNLOCKED");
    Serial.println("STATE:COMPLETED");
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
