#include <NewPing.h>
#include <Servo.h>

// Ultrasonic Sensor Pins
#define TRIGGER_PIN_FRONT 7
#define ECHO_PIN_FRONT 8
#define MAX_DISTANCE 200  // Maximum detection distance (in cm)

// Motor Pins
#define MOTOR1_PIN1 3
#define MOTOR1_PIN2 5
#define MOTOR2_PIN1 6
#define MOTOR2_PIN2 9

NewPing sonarFront(TRIGGER_PIN_FRONT, ECHO_PIN_FRONT, MAX_DISTANCE);
bool startMoving = false;  // Flag to control robot movement

void setup() {
  Serial.begin(9600); // Serial communication with Raspberry Pi
  pinMode(MOTOR1_PIN1, OUTPUT);
  pinMode(MOTOR1_PIN2, OUTPUT);
  pinMode(MOTOR2_PIN1, OUTPUT);
  pinMode(MOTOR2_PIN2, OUTPUT);
  stopMotors();
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'S') {
      startMoving = true;
    }
  }

  if (startMoving) {
    int distanceFront = sonarFront.ping_cm();

    if (distanceFront > 0 && distanceFront < 20) {
      stopMotors();
      delay(1000);
      Serial.println("OBSTACLE_FRONT");

      // Wait for Raspberry Pi's response
      char response;
      do {
        while (!Serial.available());
        response = Serial.read();
      } while (response != 'T' && response != 'D');

      delay(2000);  // Wait for 2 seconds after receiving the response

      if (response == 'T') {
        performTurnSequence();
      } else {
        moveForward();
      }
    } else {
      moveForward();
    }
  }
}

void moveForward() {
  digitalWrite(MOTOR1_PIN1, HIGH);
  digitalWrite(MOTOR1_PIN2, LOW);
  digitalWrite(MOTOR2_PIN1, HIGH);
  digitalWrite(MOTOR2_PIN2, LOW);
}

void stopMotors() {
  digitalWrite(MOTOR1_PIN1, LOW);
  digitalWrite(MOTOR1_PIN2, LOW);
  digitalWrite(MOTOR2_PIN1, LOW);
  digitalWrite(MOTOR2_PIN2, LOW);
}

void performTurnSequence() {
  for (int i = 0; i < 3; i++) {
    turnRight();
    delay(1000);
    moveForwardDistance(20);
    delay(1000);
  }
}

void turnRight() {
  digitalWrite(MOTOR1_PIN1, HIGH);
  digitalWrite(MOTOR1_PIN2, LOW);
  digitalWrite(MOTOR2_PIN1, LOW);
  digitalWrite(MOTOR2_PIN2, HIGH);
  delay(500);  // Adjust for proper turning
}

void moveForwardDistance(int distance) {
  int duration = distance * 10;
  moveForward();
  delay(duration);
  stopMotors();
}
