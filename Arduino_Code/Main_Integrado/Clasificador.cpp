#include "Clasificador.h"

Clasificador::Clasificador() {
  estadoActual = IDLE;
  servoActivo = nullptr;
}

void Clasificador::iniciar(int p1, int p2, int p3, int p4) {
  s1.attach(p1);
  s2.attach(p2);
  s3.attach(p3);
  s4.attach(p4);
  moverTodosAReposo();
}

void Clasificador::moverTodosAReposo() {
  // LADO IZQUIERDO: Servos 1 y 3 (Invertidos)
  // LADO DERECHO: Servos 2 y 4 (Normales)
  s1.write(180);
  s2.write(0);
  s3.write(180);
  s4.write(0);
}

void Clasificador::actualizar() {
  if (estadoActual == IDLE && Serial.available() > 0) {
    unsigned char act = Serial.read(); 
    char c = (char)act; 
    if (c != '\n' && c != '\r' && c != ' ') {
      procesarComando(c);
    }
  }

  unsigned long ahora = millis();

  switch (estadoActual) {
    case ESPERANDO_GOLPE:
      if (ahora - tiempoInicioEstado >= RETARDO_ANTES_ACTUAR) {
        if (servoActivo != nullptr) {
          // Determinar ángulo inicial según el servo (1 y 3 inician en 180, 2 y 4 en 0)
          anguloActual = (servoActivo == &s1 || servoActivo == &s3) ? 180 : 0;
          anguloObjetivo = 90;
          estadoActual = SALIENDO;
          tiempoUltimoPaso = ahora;
        } else {
          estadoActual = IDLE;
        }
      }
      break;

    case SALIENDO:
      // Golpe instantáneo para asegurar impacto firme y rápido contra el objeto
      anguloActual = anguloObjetivo;
      servoActivo->write(anguloActual);
      
      estadoActual = ESPERANDO_RETORNO;
      tiempoInicioEstado = ahora;
      break;

    case ESPERANDO_RETORNO:
      if (ahora - tiempoInicioEstado >= DURACION_GOLPE) {
         // Determinar el ángulo de reposo según el servo
         anguloObjetivo = (servoActivo == &s1 || servoActivo == &s3) ? 180 : 0;
         estadoActual = RETORNANDO;
         tiempoUltimoPaso = ahora;
      }
      break;

    case RETORNANDO:
      if (ahora - tiempoUltimoPaso >= PASO_MS) {
        // Mover suavemente hacia el reposo final
        if (anguloActual < anguloObjetivo) {
          anguloActual += PASO_GRADOS;
          if (anguloActual > anguloObjetivo) anguloActual = anguloObjetivo;
        } else if (anguloActual > anguloObjetivo) {
          anguloActual -= PASO_GRADOS;
          if (anguloActual < anguloObjetivo) anguloActual = anguloObjetivo;
        }
        
        servoActivo->write(anguloActual);
        tiempoUltimoPaso = ahora;

        if (anguloActual == anguloObjetivo) {
           estadoActual = IDLE;
           servoActivo = nullptr;
        }
      }
      break;
      
    case IDLE:
      break;
  }
}

void Clasificador::procesarComando(char tipo) {
  switch (tipo) {
    case '1': servoActivo = &s1; break;
    case '2': servoActivo = &s2; break;
    case '3': servoActivo = &s3; break;
    case '4': servoActivo = &s4; break;
    default: return;
  }
  estadoActual = ESPERANDO_GOLPE;
  tiempoInicioEstado = millis();
}
