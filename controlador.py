from gpiozero import DigitalInputDevice, PWMOutputDevice
from time import time_ns
from queue import Queue
from collections import deque
from socketio import Client

### Definições

# 10250 pulsos por volta   ->  1631.33 pulsos por rad
PULSES_PER_RAD            = 9250 / 6.28 #1631.33
CONTROL_CYCLE_TIME_NS     = 0.05 * 10**6
INTERFACE_CYCLE_TIME_NS   = 100 * 10**6
SPEED_CONTROL             = 0
POSITION_CONTROL          = 1
MAX_ERROR                 = 1 / PULSES_PER_RAD
CLOCKWISE                 = 0
COUNTER_CLOCKWISE         = 1

### Variaveis
position_array = deque(maxlen=2)
speed_array    = deque(maxlen=2)

encoder_1_new = 0
encoder_1_old = 0
encoder_2_new = 0
encoder_2_old = 0

posicao_ref       = 0
velocidade_ref    = 0
contador_pulsos = 0

direction = CLOCKWISE

### Socket
sio = Client()
sio.connect('http://localhost:5000')

@sio.on('comando_controle')
def receber_comando(data):
    global posicao_ref, velocidade_ref
    posicao_ref = data['posicao']
    velocidade_ref = data['velocidade']


### Timers
control_timer = time_ns()
interface_timer = time_ns()
delta_time_control = 0
delta_time_interface = 0

### IOs entrada
encoder_1 = DigitalInputDevice(23, pull_up=True)
encoder_2 = DigitalInputDevice(24, pull_up=True)


### IOs saida
motor_clockwise = PWMOutputDevice(12, frequency=1000)
motor_counterclockwise  = PWMOutputDevice(13, frequency=1000)

def le_encoders():
    global encoder_1_new, encoder_2_new

    encoder_1_new = encoder_1.value
    encoder_2_new = encoder_2.value

def define_posicao():
    global contador_pulsos, encoder_1_new, encoder_1_old

    if direction == CLOCKWISE and encoder_1_new != encoder_1_old:
        delta_position = 1 / PULSES_PER_RAD
        contador_pulsos += 1
    elif direction == COUNTER_CLOCKWISE and encoder_1_new != encoder_1_old:
        delta_position = -1 / PULSES_PER_RAD
        contador_pulsos -= 1
    else:
        delta_position = 0

    encoder_1_old = encoder_1_new
    new_position = position_array[0] + delta_position 
    position_array.appendleft(new_position)


def define_velocidade():
    p = 1000  ## polo
    T = CONTROL_CYCLE_TIME_NS * 10**(-9)
    a0 = (p*T - 2) / (2 + p*T)
    b0 = 2 / (2 + p*T)
    b1 = - 2 / (2 + p*T)

    velocidade = -a0 * speed_array[0] + b0 * position_array[0] + b1 * position_array[1]
    speed_array.appendleft(velocidade)

def controller():
    global motor_counterclockwise, motor_clockwise, direction
    erro_velocidade = velocidade_ref - speed_array[0]
    erro_posicao    = posicao_ref - position_array[0]

    if erro_posicao > MAX_ERROR:
        direction               = CLOCKWISE
        motor_clockwise.value     = 0.3
        motor_counterclockwise.value = 0.0
    elif erro_posicao < -MAX_ERROR:
        direction               = COUNTER_CLOCKWISE
        motor_counterclockwise.value = 0.3
        motor_clockwise.value     = 0.0
    else:
        motor_counterclockwise.value = 0.0
        motor_clockwise.value     = 0.0

def motor_simulation():
    pass

if __name__ == "__main__":
    le_encoders()

    position_array.appendleft(0)
    position_array.appendleft(0)
    speed_array.appendleft(0)
    speed_array.appendleft(0)

    while True:
        delta_time_control   = time_ns() - control_timer
        delta_time_interface = time_ns() - interface_timer
        
        if True: # delta_time_control >= CONTROL_CYCLE_TIME_NS:
            le_encoders()

            define_posicao()
            define_velocidade()

            controller()
            
            control_timer = time_ns()
            delta_time_control = 0
        
        # if  delta_time_interface >= INTERFACE_CYCLE_TIME_NS:
        #     ## Atualiza a interface
        #     sio.emit('telemetria_objeto', {
        #         'posicao': position_array[0], 
        #         'velocidade': speed_array[0]
        #     })

        #     # print(contador_pulsos)

        #     interface_timer = time_ns()
        #     delta_time_control = 0
