int data = 1;

void setup() {
  Serial.begin(9600);

}

void loop() {
  for (int j=0;j<3;j++) {
    Serial.print(data);
    Serial.print(" ");
    data += 1;
  }
  Serial.println();
  delay(1000);

}
