import time
import board
import touchio
import digitalio
import adafruit_max9744
import busio

# Define o pino para o sensor de capacitância
capacitance_pin = board.A2
# Define o pino para a saída de frequência
frequency_output_pin = board.D7


# --- Configuração do Amplificador ---
i2c = busio.I2C(board.SCL, board.SDA)

try:
    amp = adafruit_max9744.MAX9744(i2c)
    print("Amplifier successfully initialized!")
except ValueError as e:
    print(f"An error occurred: {e}")
    print("Make sure to connect the amplifier correctly!")
    amp = None

# Inicializa o sensor de toque
touch = touchio.TouchIn(capacitance_pin)

# Inicializa o pino de saída de frequência
frequency_port = digitalio.DigitalInOut(frequency_output_pin)
frequency_port.direction = digitalio.Direction.OUTPUT


# --- Parâmetros ---
MAX_VOLUME = 63
VOLUME_VARIATION_PER_SEC = 3
TOUCH_MULTIPLIER = 1.5
TOTAL_CALIBRATION_ROUNDS = 50
CALIBRATION_WAITING_TIME = 3
DEBOUNCE_TIME = 0.05
DESIRED_FREQUENCY = 16

# --- Variáveis Globais de Calibração e de Estado ---
CALIBRATION_NONE_CONNECTED = 0
CAPACITANCE_MIN_TOUCH_THRESHOLD = 0
current_volume = 0
last_volume_change_time = time.monotonic()


# --- Variáveis de Geração de Frequência ---
DF_PERIOD = 1.0 / DESIRED_FREQUENCY
DFP_HALF = DF_PERIOD / 2.0
last_toggle_time = time.monotonic()


def autoCalibrate():
    global CALIBRATION_NONE_CONNECTED

    print(f"\n--- Calibração Automática Começando em {CALIBRATION_WAITING_TIME} segundos ---")
    print("Por favor, mantenha sua mão longe do sensor durante a calibração.")
    time.sleep(CALIBRATION_WAITING_TIME)

    print(f"Fazendo {TOTAL_CALIBRATION_ROUNDS} leituras de linha de base...")
    
    readings = []
    for i in range(TOTAL_CALIBRATION_ROUNDS):
        raw_value = touch.raw_value
        readings.append(raw_value)
        print(f"  Leitura {i+1}/{TOTAL_CALIBRATION_ROUNDS}: {raw_value}")
        time.sleep(0.02)

    if readings:
        CALIBRATION_NONE_CONNECTED = sum(readings) // len(readings)
    else:
        CALIBRATION_NONE_CONNECTED = 0

    print(f"Calibração Automática Concluída:")
    print(f"  Linha de Base Calibrada (sem conexão): {CALIBRATION_NONE_CONNECTED}")

def detectTouchViaCapacitance(raw_value):
    global CAPACITANCE_MIN_TOUCH_THRESHOLD

    CAPACITANCE_MIN_TOUCH_THRESHOLD = int(CALIBRATION_NONE_CONNECTED * TOUCH_MULTIPLIER)
    
    return (raw_value >= CAPACITANCE_MIN_TOUCH_THRESHOLD)


def main():
    global last_toggle_time, last_volume_change_time, current_volume

    print("Gestor de Volume de Amplificador por meio do Toque")
    try:
        printablePinName = capacitance_pin.id
    except AttributeError:
        printablePinName = str(capacitance_pin)

    print(f"Sensing on GPIO pin {printablePinName}")

    autoCalibrate()

    while True:
        # Lê o valor do sensor de toque
        raw_value = touch.raw_value
        isTouching = detectTouchViaCapacitance(raw_value) 
        time.sleep(DEBOUNCE_TIME)

        if amp:
            current_time = time.monotonic()
            time_elapsed_since_last_change = current_time - last_volume_change_time

            if time_elapsed_since_last_change >= 1.0: 
                if isTouching:
                    current_volume = min(MAX_VOLUME, current_volume + VOLUME_VARIATION_PER_SEC)
                else:
                    current_volume = max(0, current_volume - VOLUME_VARIATION_PER_SEC)

                try:
                    amp.volume = current_volume
                    print(f"Volume atual: {current_volume}")
                except Exception as e:
                    print(f"Erro ao definir o volume: {e}")
                
                last_volume_change_time = current_time

        else:
            print("Nenhum amplificador detectado!")
        
        # Geração de frequência não bloqueadora
        current_time_freq = time.monotonic()
        if (current_time_freq - last_toggle_time) >= DFP_HALF:
            frequency_port.value = not frequency_port.value
            last_toggle_time = current_time_freq

        time.sleep(0.05)

if __name__ == "__main__":
    main()
