from matisse import Matisse
from time import sleep

matisse = Matisse()
print(f"IDN: {matisse.query('IDN?')}")
matisse.stabilize_on(737.747, 0.001)
sleep(15)
matisse.stabilize_off()
matisse.wavemeter.close()
