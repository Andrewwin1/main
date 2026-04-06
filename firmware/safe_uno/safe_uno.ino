const char* puzzle_name = "safe";

// Состояния: 0 = active, 1 = completed
byte puzzle_state = 0;

int pins[3] = {2, 4, 5};
int right_way[3] = {1, 0, 1};  // пример комбинации, заменить на нужную
bool solved = false;

void setup() {
  Serial.begin(115200);
  while (!Serial);
  for (int i = 0; i < 3; i++) {
    pinMode(pins[i], INPUT_PULLUP);
  }
  // Отправляем начальное состояние
  Serial.println("STATE:ACTIVE");
}

void loop() {
  // Читаем команды от ESP
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "SET_STATE:ACTIVE") {
      puzzle_state = 0;
      solved = false;
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

  bool all_match = true;
  for (int i = 0; i < 3; i++) {
    bool pressed = read_butt(pins[i]);
    if (pressed != right_way[i]) all_match = false;
  }

  if (all_match && !solved) {
    solved = true;
    puzzle_state = 1;
    Serial.println("UNLOCKED");
    Serial.println("STATE:COMPLETED");
  }
}

bool read_butt(int pin) {
  int count = 0;
  for (int i = 0; i < 50; i++) {
    count += digitalRead(pin);
    delay(1);
  }
  if (count > 40) return true;
  return false;
}
