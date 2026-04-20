import lgpio
import time

# Configuración
chip = lgpio.gpiochip_open(0)
servo_pin = 13  # Pin GPIO al que está conectado el servomotor

lgpio.gpio_claim_output(chip, servo_pin)


def mover_servo(pulse_width):
    lgpio.tx_servo(chip, servo_pin, pulse_width)
    time.sleep(1)  # Esperamos 1 segundo para que el servo se mueva


try:
    # Mueve el servo a 0 grados
    print("Moviendo a 0 grados")
    mover_servo(500)

    # Mueve el servo a 90 grados
    print("Moviendo a 90 grados")
    mover_servo(1500)

    # Mueve el servo a 180 grados
    print("Moviendo a 180 grados")
    mover_servo(2500)

finally:
    lgpio.tx_servo(chip, servo_pin, 0)  # Detener servo
    lgpio.gpiochip_close(chip)  # Cerrar el chip
