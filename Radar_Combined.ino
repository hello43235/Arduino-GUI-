#include <Servo.h>

Servo myservo;
String pypos;

int trigPin = 12;  // Trigger
int echoPin = 11;  // Echo
int pos = 0;
long duration;
float cm;
char userInput;

void setup() {
  //Serial Port begin
  Serial.begin(9600);
  Serial.setTimeout(10);
  myservo.attach(9);
  //Define inputs and outputs

  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
}

void loop() {
  // The sensor is triggered by a HIGH pulse of 10 or more microseconds.
  // Give a short LOW pulse beforehand to ensure a clean HIGH pulse:

  digitalWrite(trigPin, LOW);
  delayMicroseconds(5);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  // Read the signal from the sensor: a HIGH pulse whose
  // duration is the time (in microseconds) from the sending
  // of the ping to the reception of its echo off of an object.
  pinMode(echoPin, INPUT);
  duration = pulseIn(echoPin, HIGH);

  // Convert the time into a distance
  cm = (duration / 2) * 0.0343;  // Divide by 29.1 or multiply by 0.0343


  Serial.print(cm);
  Serial.println();

  if (cm <= 10){
    delay(2);
  } else if (cm <= 50) {
    delay(4);
  } else if (cm <= 100) {
    delay(7);
  } else if (cm <= 150) {
    delay(9);
  } else if (cm <= 200) {
    delay(12);
  } else if (cm <= 250) {
    delay(15);
  } else if (cm <= 300) {
    delay(18);
  } else if (cm <= 350) {
    delay(21);
  } else if (cm <= 400) {
    delay(24);
  } else if (cm <= 450) {
    delay(27);
  } else {
    delay(47);
  }

  if (Serial.available()) {
    pypos = Serial.readStringUntil('\n');
    int pyposint = pypos.toInt();
    myservo.write(pyposint);
    delay(2);
  }
  else {
    delay(2);
  }
}