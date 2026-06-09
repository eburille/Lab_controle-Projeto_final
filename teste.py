from collections import deque

fifo = deque(maxlen=3)

fifo.appendleft(1)

fifo.appendleft(2)
print(list(fifo))

fifo.appendleft(3)
print(list(fifo))

fifo.appendleft(4)
print(list(fifo))
print(fifo[0])
