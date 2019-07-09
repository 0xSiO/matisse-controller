from matisse import Matisse
from time import sleep

matisse = Matisse()
print(f"IDN: {matisse.query('IDN?')}")
matisse.stabilize_on(0.15)
sleep(3)
matisse.stabilize_off()
