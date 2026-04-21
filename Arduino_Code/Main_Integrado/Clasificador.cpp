#include "Clasificador.h"

Clasificador::Clasificador() {
  estadoActual = IDLE;
  servoActivo = nullptr;
}

void Clasificador::iniciar(int p1, int p2, int p3, int p4) {
  _p1 = p1; _p2 = p2; _p3 = p3; _p4 = p4;
  s1.attach(p1);
  s2.attach(p2);
  s3.attach(p3);
  s4.attach(p4);
  moverTodosAReposo();
}

void Clasificador::moverTodosAReposo() {
  // LADO IZQUIERDO: Servos 1 y 3 (Invertidos) -> Límite acolchado en 175
  // LADO DERECHO: Servos 2 y 4 (Normales) -> Límite acolchado en 5
  s1.write(175);
  s2.write(5);
  s3.write(175);
  s4.write(5);
  
  // Esperar a que lleguen físicamente en el arranque y luego cortar corriente
  delay(600);
  s1.detach();
  s2.detach();
  s3.detach();
  s4.detach();
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
          // Determinar ángulo inicial según el servo con padding de 5 grados para evitar temblores
          anguloActual = (servoActivo == &s1 || servoActivo == &s3) ? 175 : 5;
          anguloObjetivo = 90;
          
          // RE-CONECTAR ELECTRICAMENTE EL SERVO ACTIVO JUSTO ANTES DE MOVERLO
          if (servoActivo == &s1) s1.attach(_p1);
          else if (servoActivo == &s2) s2.attach(_p2);
          else if (servoActivo == &s3) s3.attach(_p3);
          else if (servoActivo == &s4) s4.attach(_p4);
          
          estadoActual = SALIENDO;
          tiempoUltimoPaso = ahora;
        } else {
          estadoActual = IDLE;
        }
      }
      break;

    case SALIENDO:
      // Movimiento de golpe instantaneo
      anguloActual = anguloObjetivo;
      servoActivo->write(anguloActual);
      estadoActual = ESPERANDO_RETORNO;
      tiempoInicioEstado = ahora;
      break;

    case ESPERANDO_RETORNO:
      if (ahora - tiempoInicioEstado >= DURACION_GOLPE) {
         // Determinar el ángulo de reposo según el servo con margen de parada suave
         anguloObjetivo = (servoActivo == &s1 || servoActivo == &s3) ? 175 : 5;
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
           // CORTAR ELECTRICIDAD AL LLEGAR AL LIMITE PARA MATAR EL ZARANDEO FANTASMA
           servoActivo->detach();
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
