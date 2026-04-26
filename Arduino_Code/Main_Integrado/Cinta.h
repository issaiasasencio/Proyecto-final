#ifndef CINTA_H
#define CINTA_H

#include <Arduino.h>
#include <AccelStepper.h>

class Cinta {
  private:
    AccelStepper* motor;
    int pinPotenciometro;

  public:
    Cinta(int stepPin, int dirPin, int potPin);
    void iniciar();
    void actualizar();
    void setVelocidad(float v);
    void setModoManual(bool m);
    void setParadaEmergencia(bool p);

  private:
    float velocidadExterna = -1; 
    bool modoManual = false;
    bool paradaEmergencia = false;
};

#endif
