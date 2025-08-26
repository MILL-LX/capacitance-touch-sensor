import time
import board
import touchio
import audiobusio
import array
import math
import adafruit_max9744
import audiocore
import busio
import analogio


# Define o pino para o sensor de capacitância
capacitance_pin = board.A2
# Define o pino para a saída de frequência
sound_output = board.D7
# Define o pino para o potenciômetro
potentiometer_pin = board.A1


# --- Configuração do Amplificador ---
i2c = busio.I2C(board.SCL, board.SDA)

try:
    amp = adafruit_max9744.MAX9744(i2c)
    print("MAX9744 Amplifier initialized successfully.")
except ValueError as e:
    print(f"Error initializing amplifier: {e}")
    print("Make sure the amplifier is properly connected via I2C.")
    amp = None 

# --- Fim da Configuração do Amplificador ---


# Inicializa o sensor de toque
touch_sensor = touchio.TouchIn(capacitance_pin)

# Inicializa o potenciômetro
potentiometer = analogio.AnalogIn(potentiometer_pin)


# --- Parâmetros de Calibração Automática ---
CALIBRATION_READINGS = 50       # Número de leituras para calibração
CALIBRATION_DELAY_SECONDS = 3   # Atraso antes de começar a calibração
CALIBRATION_MAX_CAP_PF = 100.0   # Capacitância máxima para mapeamento

# Os multiplicadores de sensibilidade agora são ajustados pelo potenciômetro.
# Estes são os limites MÍNIMO e MÁXIMO que o potenciômetro pode definir.
MIN_MULTIPLIER = 1.2  # Sensibilidade mais alta (toque leve)
MAX_MULTIPLIER = 5.0  # Sensibilidade mais baixa (toque forte)

# --- Fim dos Parâmetros de Calibração ---


# Debounce para os pinos de toque ou sensoriamento 
DEBOUNCE_TIME = 0.05

# Variáveis globais para valores calibrados
CALIBRATION_NONE_CONNECTED = 0
CALIBRATION_TOUCH_THRESHOLD_VALUE = 0


# --- Variáveis de Geração de Frequência ---
FREQUENCY = 16  # Hz
PERIOD = 1.0 / FREQUENCY
HALF_PERIOD = PERIOD / 2.0

bclk = board.D8
lrclk = board.D10
sRate = 8e3
length = sRate // FREQUENCY
volume = 0.5
sine_wave = array.array("h", [0] * length)
for i in range(length):
    sine_wave[i] = int((1 + math.sin(math.pi * 2 * i / length)) * volume * (2**15 - 1))

audio = audiocore.RawSample(sine_wave, sample_rate=sRate)
i2s = audiobusio.I2SOut(bclk, lrclk, sound_output)

def auto_calibrate():
    global CALIBRATION_NONE_CONNECTED, CALIBRATION_TOUCH_THRESHOLD_VALUE

    print(f"\n--- Calibração Automática Começando em {CALIBRATION_DELAY_SECONDS} segundos ---")
    print("Por favor, mantenha sua mão longe do sensor durante a calibração.")
    time.sleep(CALIBRATION_DELAY_SECONDS)

    print(f"Fazendo {CALIBRATION_READINGS} leituras de linha de base...")
    
    readings = []
    for i in range(CALIBRATION_READINGS):
        raw_value = touch_sensor.raw_value
        readings.append(raw_value)
        print(f"  Leitura {i+1}/{CALIBRATION_READINGS}: {raw_value}")
        time.sleep(0.02)

    if readings:
        CALIBRATION_NONE_CONNECTED = sum(readings) // len(readings)
    else:
        CALIBRATION_NONE_CONNECTED = 0

    print(f"Calibração Automática Concluída:")
    print(f"  Linha de Base Calibrada (sem conexão): {CALIBRATION_NONE_CONNECTED}")
    print(f"  Capacitância Máxima Assumida para Mapeamento: {CALIBRATION_MAX_CAP_PF} pF\n")


def calculate_capacitance_from_touchio(raw_value, touch_multiplier):

    #Aproxima a capacitância com base no valor bruto do touchio usando escalonamento linear
    #em relação à linha de base calibrada e a um limite de toque ajustável.
 
    global CALIBRATION_TOUCH_THRESHOLD_VALUE
    
    # Recalcula o limite de toque a cada ciclo com base no multiplicador atual do potenciômetro
    CALIBRATION_TOUCH_THRESHOLD_VALUE = int(CALIBRATION_NONE_CONNECTED * touch_multiplier)

    clamped_raw_value = max(raw_value, CALIBRATION_NONE_CONNECTED)
    delta_raw = clamped_raw_value - CALIBRATION_NONE_CONNECTED
    
    raw_range = CALIBRATION_TOUCH_THRESHOLD_VALUE - CALIBRATION_NONE_CONNECTED

    if raw_range <= 0:
        return 0.0

    approx_capacitance_pf = (delta_raw / raw_range) * CALIBRATION_MAX_CAP_PF
    
    if approx_capacitance_pf > CALIBRATION_MAX_CAP_PF:
        approx_capacitance_pf = CALIBRATION_MAX_CAP_PF

    return approx_capacitance_pf


def main():

    print("Medidor de Capacitância com Controle de Sensibilidade por Potenciômetro")
    try:
        pin_name_to_print = capacitance_pin.id
    except AttributeError:
        pin_name_to_print = str(capacitance_pin)

    print(f"Sensing on GPIO pin {pin_name_to_print}")

    auto_calibrate()

    while True:
        # --- Leitura do Potenciômetro ---
        # O valor bruto vai de 0 a 65535. Mapeie para a faixa de sensibilidade desejada.
        pot_value = potentiometer.value
        touch_multiplier = ((pot_value / 65535) * (MAX_MULTIPLIER - MIN_MULTIPLIER)) + MIN_MULTIPLIER
        
        # --- Leitura do Sensor de Capacitância ---
        raw_value = touch_sensor.raw_value
        time.sleep(DEBOUNCE_TIME)
        approx_capacitance_pf = calculate_capacitance_from_touchio(raw_value, touch_multiplier)

        # --- Ajuste de Volume do Amplificador ---
        if amp:
            min_cap_for_volume = 0.0
            max_cap_for_volume = CALIBRATION_MAX_CAP_PF
            if max_cap_for_volume == min_cap_for_volume:
                volume = 0
            else:
                volume_float = (approx_capacitance_pf - min_cap_for_volume) / (max_cap_for_volume - min_cap_for_volume) * 63.0
                volume = int(max(0, min(63, volume_float)))

            try:
                amp.volume = volume
                print(f"Potenciômetro: {pot_value} (Multiplicador: {touch_multiplier:.2f}), Capacitância: {approx_capacitance_pf:.2f} pF, Volume: {volume}")
            except Exception as e:
                print(f"Erro ao definir o volume: {e}")
                print(f"Capacitância: {approx_capacitance_pf:.2f} pF")
        else:
            print(f"Potenciômetro: {pot_value} (Multiplicador: {touch_multiplier:.2f}), Capacitância: {approx_capacitance_pf:.2f} pF (Amplificador não conectado)")

        # --- Geração de Frequência Não Bloqueadora ---
        """current_time = time.monotonic()
        if (current_time - last_frequency_toggle_time) >= HALF_PERIOD:
            frequency_port.value = not frequency_port.value
            last_frequency_toggle_time = current_time
        """
        i2s.play(audio, loop=True)
        # --- End Frequency Generation ---

if __name__ == "__main__":
    main()
    
""""""