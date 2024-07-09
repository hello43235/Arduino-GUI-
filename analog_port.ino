
int trigPin = 12;  // Trigger
int echoPin = 11;  // Echo
int ldr = A9;
int Echo = 28;

int samples[75];
//int samples[sample_size];
long duration, cm, inches;
boolean flag;

void setup() {
  //Serial Port begin
  Serial.begin(115200);

  //Define inputs and outputs

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(Echo, INPUT);
  pinMode(ldr, INPUT);
  digitalWrite(trigPin, LOW);
}

void loop() {
  while (!Serial.available()) {}

  // The sensor is triggered by a HIGH pulse of 10 or more microseconds.
  // Give a short LOW pulse beforehand to ensure a clean HIGH pulse:
  //if (Serial.available()) {
    //String pypos = Serial.readStringUntil('\n');
  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  delayMicroseconds(500);
  //}
  // Read the signal from the sensor: a HIGH pulse whose
  // duration is the time (in microseconds) from the sending
  // of the ping to the reception of its echo off of an object.
  flag = false;
  //while (!flag)
  //{
  
  //if (digitalRead(echoPin)) {
  for(int i=0; i<75; i++) {
    int data = analogRead(ldr);
    samples[i] = data;
    //Serial.print(data);
    //Serial.print('\n');
    //delayMicroseconds(1);
    }
  for(int i=0; i<75; i++) {
    Serial.print(samples[i]);
    Serial.print('\n');
    //delayMicroseconds(50);
  }
  delay(10);
    //flag = true;
  //}
  //}
  //delay(10);
}