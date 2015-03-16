import Adafruit_BBIO.GPIO as gpio

class PinesFPGA:
  
  def __init__(self):
    pines = ["P8_8","P8_10","P8_12","P8_14","P8_16", "P8_18", "P8_7", "P8_9", "P8_11", "P8_13", "P8_17"]
    for i in pines:
      gpio.setup(i, gpio.OUT)
      gpio.output(i, gpio.LOW)
    self.reset(True)
  
  def setLength1(self, length):
    if length == 0:
      gpio.output("P8_8", gpio.LOW)
      gpio.output("P8_10", gpio.LOW)
    elif length == 1:
      gpio.output("P8_8", gpio.LOW)
      gpio.output("P8_10", gpio.HIGH)
    elif length == 2:
      gpio.output("P8_8", gpio.HIGH)
      gpio.output("P8_10", gpio.LOW)
    elif length == 3:
      gpio.output("P8_8", gpio.HIGH)
      gpio.output("P8_10", gpio.HIGH)
  
  def setRate1(self, rate):
    if rate == 0:
      gpio.output("P8_12", gpio.LOW)
      gpio.output("P8_14", gpio.LOW)
    elif rate == 1:
      gpio.output("P8_12", gpio.LOW)
      gpio.output("P8_14", gpio.HIGH)
    elif rate == 2:
      gpio.output("P8_12", gpio.HIGH)
      gpio.output("P8_14", gpio.LOW)
    elif rate == 3:
      gpio.output("P8_12", gpio.HIGH)
      gpio.output("P8_14", gpio.HIGH)
  
  def setLength2(self, length):
    if length == 0:
      gpio.output("P8_7", gpio.LOW)
      gpio.output("P8_9", gpio.LOW)
    elif length == 1:
      gpio.output("P8_7", gpio.LOW)
      gpio.output("P8_9", gpio.HIGH)
    elif length == 2:
      gpio.output("P8_7", gpio.HIGH)
      gpio.output("P8_9", gpio.LOW)
    elif length == 3:
      gpio.output("P8_7", gpio.HIGH)
      gpio.output("P8_9", gpio.HIGH)
  
  def setRate2(self, rate):
    if rate == 0:
      gpio.output("P8_11", gpio.LOW)
      gpio.output("P8_13", gpio.LOW)
    elif rate == 1:
      gpio.output("P8_11", gpio.LOW)
      gpio.output("P8_13", gpio.HIGH)
    elif rate == 2:
      gpio.output("P8_11", gpio.HIGH)
      gpio.output("P8_13", gpio.LOW)
    elif rate == 3:
      gpio.output("P8_11", gpio.HIGH)
      gpio.output("P8_13", gpio.HIGH)
  
  def setClock(self, clock):
    if clock == 1:
      gpio.output("P8_16", gpio.LOW)
      gpio.output("P8_18", gpio.LOW)
    if clock == 2:
      gpio.output("P8_16", gpio.HIGH)
      gpio.output("P8_18", gpio.LOW)
    if clock == 3: #SoF1
      gpio.output("P8_16", gpio.LOW)
      gpio.output("P8_18", gpio.HIGH)
    if clock == 4: #SoF2
      gpio.output("P8_16", gpio.HIGH)
      gpio.output("P8_18", gpio.HIGH)
  
  def reset(self, state):
    if state:
      gpio.output("P8_17", gpio.LOW)
      for i in range(100): # Perdemos tiempo
        a = i+1
      gpio.output("P8_17" , gpio.HIGH)
    else:
      gpio.output("P8_17" , gpio.HIGH)
  
  def quitGPIO(self):
    gpio.cleanup()


'''
def main():
  pines = PinesFPGA()
  print("inicializado")
  #pines.reset(True)
  pines.setClock(1)
  pines.setRate(3)
  pines.setLength(3)
  #pines.quitGPIO()
  while True:
    a = 5
  print("fin")

if __name__ == '__main__':
  main()'''
