#include "Cinta.h"

Cinta::Cinta(int stepPin, int dirPin, int potPin) {
  motor = new AccelStepper(1, stepPin, dirPin);
  pinPotenciometro = potPin;
}

void Cinta::iniciar() {
  pinMode(pinPotenciometro, INPUT);
  motor->setMaxSpeed(3000); 
}

void Cinta::actualizar() {
  int potValue = analogRead(pinPotenciometro);

  if (potValue < 50) {
    motor->setSpeed(0);
  } else {
    // Mapeo de velocidad: de 200 a 3000 pasos/segundo
    float velocidad = map(potValue, 50, 1023, 200, 3000);
    motor->setSpeed(velocidad);
  }

  motor->runSpeed();
}