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
  float velocidad = 0;

  if (paradaEmergencia) {
    velocidad = 0;
  } else if (modoManual) {
    int potValue = analogRead(pinPotenciometro);
    if (potValue >= 50) {
      velocidad = map(potValue, 50, 1023, 200, 3000);
    }
  } else if (velocidadExterna >= 0) {
    velocidad = velocidadExterna;
  }

  motor->setSpeed(velocidad);
  motor->runSpeed();
}

void Cinta::setVelocidad(float v) {
  velocidadExterna = v;
}

void Cinta::setModoManual(bool m) {
  modoManual = m;
}

void Cinta::setParadaEmergencia(bool p) {
  paradaEmergencia = p;
}