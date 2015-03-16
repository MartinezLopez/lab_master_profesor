import Adafruit_BBIO.UART as uart
import serial
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu


class Modbus:
  
  def __init__(self):
    uart.setup("UART1")
    
    self.master = modbus_rtu.RtuMaster(serial.Serial(port="/dev/ttyO1", baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
    self.master.set_timeout(5.0)
    self.master.set_verbose(False)
  
  def write_registers(self, slaveAddress, firstRegister, data):
    self.master.execute(slaveAddress, cst.WRITE_MULTIPLE_REGISTERS, firstRegister, output_value=data)
  
  def read_registers(self, slaveAddress, firstRegister, numRegisters):
    val = self.master.execute(slaveAddress, cst.READ_HOLDING_REGISTERS, firstRegister, numRegisters)
    return val


'''
def main(): 
  mb = Modbus()
  mb.write_registers(0x02, 1, [200, 0, 250])
  val = mb.read_registers(0x02, 0, 2)
  for i in range(len(val)):
    print val[i]

if __name__ == '__main__':
  main()
'''
