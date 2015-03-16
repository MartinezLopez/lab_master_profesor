#!/usr/bin/python

from Osciloscopio import *
from Ventana import *
import os

def get_osc_id():
  ''' Obtiene el idVendor y el idProduct del primer dispositivo Tektronix que encuentre.
  
  Mediante el comando lsusb elige el primer dispositivo Tektronix conectado.
  Selecciona las posiciones de la cadena de caracteres que nos interesan y les da el formato que necesitamos para identificar el osciloscopio con python-usbtmc.
  
  '''
  usb = os.popen("lsusb | grep Tektronix") #Vemos los dispositivos conectados y elegimos el Tektronix
  id = usb.read()
  id = id[23:32] #Nos quedamos con el id del fabricante y del aparato
  id = id.replace(':', '::0x') #Ajustamos el formato al que necesitamos
  id = '0x' + id
  return id

def main():
  '''Punto de entrada de la aplicacion.
  
  Obtiene el identificador del osciloscopio y con el crea un objeto de la clase Osciloscopio.
  Crea un objeto de la clase VentanaPrincipal para iniciar la GUI.
  
  '''
  osc_id = get_osc_id()
  app = QtGui.QApplication(sys.argv)
  app.setStyle("cleanlooks")
  osc = Osciloscopio(osc_id)
  main_window = VentanaPrincipal(osc)
  osc_control = VentanaConfiguracion(osc)
  pines_contro = VentanaConfigIO()
  sys.exit(app.exec_())

if __name__ == '__main__':
  main()
