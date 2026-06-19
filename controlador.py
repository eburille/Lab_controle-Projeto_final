from gpiozero import DigitalInputDevice, PWMOutputDevice
from time import time_ns, sleep
from queue import Queue
from collections import deque
import multiprocessing as mp
from multiprocessing.connection import Connection
import os

### Definições

# 10250 pulsos por volta   ->  1631.33 pulsos por rad
PULSES_PER_RAD            = 21000 / 6.28 #1631.33
CONTROL_CYCLE_TIME_NS     = 0.05 * 10**6
INTERFACE_CYCLE_TIME_NS   = 500 * 10**6
SPEED_CONTROL             = 0
POSITION_CONTROL          = 1
MAX_ERROR                 = 1 / PULSES_PER_RAD
CLOCKWISE                 = 0
COUNTER_CLOCKWISE         = 1
ENCODER_SEQUENCY          = [1, 3, 2, 0]

### Variaveis
position_array = deque(maxlen=2)
speed_array    = deque(maxlen=2)
vetor_comb_encoder = deque(maxlen=2)

new_ind_encoder = 0
ind_encoder = 0
next_ind_encoder = 0
previous_ind_encoder = 0
next2_ind_encoder = 0
previous2_ind_encoder = 0

nova_comb_encoder = 0
encoder_1_new = 0
encoder_1_old = 0
encoder_2_new = 0
encoder_2_old = 0

posicao_ref       = 0
velocidade_ref    = 0
contador_pulsos = 0

direction = CLOCKWISE

### Timers
control_timer = time_ns()
interface_timer = time_ns()
delta_time_control = 0
delta_time_interface = 0

### IOs entrada
encoder_1 = 0 # DigitalInputDevice(23, pull_up=True)
encoder_2 = 0 # DigitalInputDevice(24, pull_up=True)


### IOs saida
motor_clockwise = 0 # PWMOutputDevice(12, frequency=1000)
motor_counterclockwise  = 0 # PWMOutputDevice(13, frequency=1000)

def le_encoders():
    global encoder_1_new, encoder_2_new, nova_comb_encoder, new_ind_encoder

    encoder_1_new = encoder_1.value
    encoder_2_new = encoder_2.value

    nova_comb_encoder = encoder_1_new + (encoder_2_new << 1) 
    new_ind_encoder = ENCODER_SEQUENCY.index(nova_comb_encoder)

def define_posicao():
    global contador_pulsos, encoder_1_new, encoder_1_old, next_ind_encoder, previous_ind_encoder, ind_encoder, next2_ind_encoder, previous2_ind_encoder

    if new_ind_encoder == next_ind_encoder:
        delta_position = 1 / PULSES_PER_RAD
    elif new_ind_encoder == previous_ind_encoder:
        delta_position = -1 / PULSES_PER_RAD
    elif new_ind_encoder == next2_ind_encoder:
        delta_position = 2 / PULSES_PER_RAD
    elif new_ind_encoder == previous2_ind_encoder:
        delta_position = -2 / PULSES_PER_RAD
    elif new_ind_encoder == ind_encoder:
        delta_position = 0
    else:
        delta_position = 0
        print("erro")

    encoder_1_old = encoder_1_new
    new_position = position_array[0] + delta_position 
    position_array.appendleft(new_position)

    ind_encoder = new_ind_encoder
    next_ind_encoder = (new_ind_encoder + 1) & 3
    previous_ind_encoder = (new_ind_encoder - 1) & 3
    next2_ind_encoder = (next_ind_encoder + 1) & 3
    previous2_ind_encoder = (previous_ind_encoder - 1) & 3


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

    if erro_posicao > MAX_ERROR * 15:
        direction               = CLOCKWISE
        motor_clockwise.value     = 1.0
        motor_counterclockwise.value = 0.0
        # print("horario")
    elif erro_posicao < -MAX_ERROR * 15:
        direction               = COUNTER_CLOCKWISE
        motor_counterclockwise.value = 1.0
        motor_clockwise.value     = 0.0
        # print("antihorario")
    else:
        # print("parado")
        motor_counterclockwise.value = 0.0
        motor_clockwise.value     = 0.0

def motor_simulation():
    pass


def run(pipe: Connection):
    global control_timer, interface_timer, posicao_ref, encoder_1, encoder_2, motor_clockwise, motor_counterclockwise, encoder_1, encoder_2, CONTROL_CYCLE_TIME_NS

    motor_clockwise = PWMOutputDevice(12, frequency=1000)
    motor_counterclockwise  = PWMOutputDevice(13, frequency=1000)

    motor_clockwise.value = 0.0
    motor_counterclockwise.value = 0.0

    sleep(1)
    
    encoder_1 = DigitalInputDevice(23, pull_up=True)
    encoder_2 = DigitalInputDevice(24, pull_up=True)

    le_encoders()

    position_array.appendleft(0)
    position_array.appendleft(0)
    speed_array.appendleft(0)
    speed_array.appendleft(0)
    vetor_comb_encoder.appendleft(0)
    
    while True:
        delta_time_control   = time_ns() - control_timer
        delta_time_interface = time_ns() - interface_timer
        
        if pipe.poll():
            referencia = pipe.recv()
            
            print("Referencia recebida - ", referencia)
            posicao_ref = referencia["ref_pos"]

        if delta_time_control >= CONTROL_CYCLE_TIME_NS:
            # CONTROL_CYCLE_TIME_NS = delta_time_control
            # print(delta_time_control)
            le_encoders()

            define_posicao()
            define_velocidade()

            controller()
            
            control_timer = time_ns()
            delta_time_control = 0
        
        if  delta_time_interface >= INTERFACE_CYCLE_TIME_NS:            
            pipe.send({'posicao': position_array[0], 'velocidade': speed_array[0] })


            interface_timer = time_ns()
            delta_time_interface = 0

if __name__ == "__main__":
    run()

    