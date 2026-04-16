#ifndef CLASIFICADOR_H
#define CLASIFICADOR_H

#include <Arduino.h>
#include <Servo.h>

enum EstadoServo {
  IDLE,
  ESPERANDO_GOLPE,
  GOLPEANDO
};

class Clasificador {
  private:
    Servo s1, s2, s3, s4;
    Servo* servoActivo;
    
    EstadoServo estadoActual;
    unsigned long tiempoInicioEstado;

    const int RETARDO_ANTES_ACTUAR = 100;
    const int DURACION_GOLPE = 800;

  public:
    Clasificador();
    void iniciar(int p1, int p2, int p3, int p4);
    void actualizar();
    
  private:
    void procesarComando(char c);
    void moverTodosAReposo();
};

#endif
