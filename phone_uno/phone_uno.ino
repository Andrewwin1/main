
/*
 * матрица по pins 
 *1  6  -  2
 *2  7  -  2
 *3  8  -  2
 *4  6  -  3
 *5  7  -  3
 *6  10 -  3
 *7  6  -  4
 *8  9  -  4
 *9  8  -  4
 *0  9  -  5
 */
byte pins [11] = {2, 3 , 4, 5, 6, 7, 8, 9, 10, A0, A1};
byte right_way [7] = {4, 5, 7, 8, 1, 0, 3};
byte last = 0;
byte butt = 0;
int count = 0;
byte matrix (byte f, byte s){
  if (f == 2){
    if (s == 6)  return 1;
    if (s == 7)  return 2;
    if (s == 8)  return 3; 
  }
  else if (f == 3){
    if (s == 6)  return 4;
    if (s == 7)  return 5;
    if (s == 10) return 6;
  }
  else if (f == 4){
    if (s == 6)  return 7;
    if (s == 9)  return 8;
    if (s == 8)  return 9;
  }
  else if (f == 5){
    if (s == 9)  return 0;
  }
  
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < 11; i++){
    pinMode(pins[i], INPUT_PULLUP);
  }

}

void loop() {
  if (Serial.available() > 0){
    String buff = Serial.readString();
    if (buff == "open"){
      // реле
    }
  }
  
  for (int i = 0; i < 11; i++){
    delay(10);
    pinMode(pins[i], OUTPUT);
    delay(1);
    digitalWrite(pins[i], 0);
    for (int item = 0; item < 11; item++){
      if (item == i) delay(1);
      else if (read_butt(pins[item])) {
        if (i == 2 || i == 3 || i == 4 || i == 5) butt = matrix(i, item);
        else butt = matrix(item, i);

        if (butt != last) {
          last = butt;
//          Serial.println(butt);
          if (butt == right_way[count]){
            count += 1;
          }
          else count = 0;

          if (count == 7) {
            Serial.println("end");
            count = 0;
            // отправить сигнал на реле 
          }
        }
        else {
          
        }
      }
    }
    pinMode(pins[i], INPUT_PULLUP);
    
    
  }
  
}

int read_butt(byte pin){
  int count = 0;
  for (int i = 0; i <= 50; i++){
    delayMicroseconds(20);
    count += !digitalRead(pin);
  }
  if (count > 35){
    return 1;
  }
  if (count < 15){
    return 0;
  }
}
