from time import time_ns
from queue import Queue
from collections import deque

### variaveis
RAD_PER_TICK = 1
vetor_comb_encoder = deque(maxlen=5)
vetor_posicao = deque(maxlen=5)
vetor_velocidade = deque(maxlen=5)

### Timers
CYCLE_TIME_NS = 10 * 10**6
time = time_ns()
delta_time = 0

### IOs entrada
    
encoder_1 = 0
encoder_2 = 0


### IOs saida

def le_encoders():
    encoder_1 = 1
    encoder_2 = 2

def define_posicao():
    nova_comb_encoder = encoder_1 + encoder_2 << 1
    
    nova_posicao = vetor_posicao[0] + (nova_comb_encoder - vetor_comb_encoder[0]) * RAD_PER_TICK

    vetor_comb_encoder.appendleft(nova_comb_encoder)
    vetor_posicao.appendleft(nova_posicao)

def define_velocidade():
    p = 1000  ## polo
    T = CYCLE_TIME_NS * 10**(-9)
    a0 = (p*T - 2) / (2 + p*T)
    b0 = 2 / (2 + p*T)
    b1 = - 2 / (2 + p*T)

    velocidade = -a0 * vetor_velocidade[1] + b0 * vetor_posicao[0] + b1 * vetor_posicao [1]
    vetor_velocidade.appendleft(velocidade)

def controlador():
    pass

if __name__ == "__main__":

    while True:
        while  delta_time < CYCLE_TIME_NS:
            delta_time = time_ns() - time

        le_encoders()

        define_posicao()
        define_velocidade()

        controlador()

        time = time_ns()
        delta_time = 0
