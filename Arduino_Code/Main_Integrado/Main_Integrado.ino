#include "Cinta.h"
#include "Clasificador.h"

// --- CONFIGURACIÓN DE PINES ---
const int PIN_STEP = 3; 
const int PIN_DIR  = 2;
const int PIN_POT  = A0; 

// 2. Pines de los Servos (MAPEO DEFINITIVO)
// Cercanos: 1 y 2. Lejanos: 3 y 4.
// Izquierdos (Invertidos): 1 y 3. Derechos (Normales): 2 y 4.
const int PIN_SERVO_1 = 7; // Ex Plastico (Izquierdo Cercano)
const int PIN_SERVO_2 = 5; // Ex Vidrio (Derecho Cercano)
const int PIN_SERVO_3 = 4; // Ex Metal (Izquierdo Lejano)
const int PIN_SERVO_4 = 6; // Ex Carton (Derecho Lejano)

const int PIN_BOTON = 8; // Botón Parada de Emergencia

Cinta cinta(PIN_STEP, PIN_DIR, PIN_POT);
Clasificador clasificador;

void setup() {
  Serial.begin(115200); 
  Serial.println("ARDUINO INICIADO: Sistema 4 Servos");

  pinMode(PIN_BOTON, INPUT_PULLUP);

  cinta.iniciar();
  cinta.setVelocidad(-1); // Arranca en OFF
  clasificador.iniciar(PIN_SERVO_1, PIN_SERVO_2, PIN_SERVO_3, PIN_SERVO_4);
}

String inputBuffer = "";
bool emergencyActive = false;

void loop() {
  // 1. Verificar Botón Físico (Parada de Emergencia)
  if (digitalRead(PIN_BOTON) == LOW) {
    if (!emergencyActive) {
      emergencyActive = true;
      cinta.setParadaEmergencia(true);
      Serial.println("ALERT: E-STOP PRESSED");
    }
  }

  // 2. Lectura Serial No Bloqueante
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        if (inputBuffer.startsWith("C:")) { 
          float vel = inputBuffer.substring(2).toFloat();
          cinta.setVelocidad(vel);
        } 
        else if (inputBuffer.startsWith("M:")) { // M:1 Manual, M:0 Auto
          bool manual = inputBuffer.substring(2).toInt();
          cinta.setModoManual(manual);
        }
        else if (inputBuffer.startsWith("E:0")) { // Reset Emergencia desde UI
          emergencyActive = false;
          cinta.setParadaEmergencia(false);
          Serial.println("INFO: E-STOP RESET");
        }
        else {
          clasificador.procesarComando(inputBuffer);
        }
      }
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  cinta.actualizar();  
  clasificador.actualizar_sin_serial();
}
