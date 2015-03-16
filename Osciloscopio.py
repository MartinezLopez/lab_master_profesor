#!/usr/bin/python

import usbtmc
import time
from struct import unpack
from Ventana import VentanaInfo

class Osciloscopio:
    
  def __init__(self, id):
    '''Constructor de la clase ociloscopio.
    
    Aqui se crea un objeto de la clase Osciloscopio y se inicializan los diccionarios que empleara para asegurarse de que los valores de las configuraciones son valores aceptados por el osciloscopio Tektronix 2022B.
    Tambien se asocia el objeto de la clase Osciloscopio con un osciloscopio real conectado por USB.
    Si no hubiera un osciloscopio conectado por USB la asociacion fallaria y la aplicacion terminaria.
    
    Parametros:
      id: identificador valido del osciloscopio (string de la forma 0xYYYY::0xZZZZ donde YYYY es el idVendor y ZZZZ el idProduct del osciloscopio).
    
    '''
    # Inicializamos los diccionarios para que tengan los valores validos para el osciloscopio
    self.vol_div = {"5v":'5', "2v":'2', "1v":'1', "500mv":'500e-3', "200mv":'200e-3', "100mv":'100e-3', "50mv":'50e-3', "20mv":'20e-3', "10mv":'10e-3', "5mv":'5e-3', "2mv":'2e-3'}
    self.sec_div = {"50s":'50', "25s":'25', "10s":'10', "5s":'5', "2.5s":'2.5', "1s":'1',"500ms":'500e-3', "250ms":'250e-3', "100ms":'100e-3',"50ms":'50e-3', "25ms":'25e-3', "10ms":'10e-3', "5ms":'5e-3', "2.5ms":'2.5e-3', "1ms":'1e-3', "500us":'500e-6', "250us":'250e-6', "100us":'100e-6',"50us":'50e-6', "25us":'25e-6', "10us":'10e-6', "5us":'5e-6', "2.5us":'2.5e-6', "1us":'1e-6', "500ns":'500e-9', "250ns":'250e-9', "100ns":'100e-9',"50ns":'50e-9', "25ns":'25e-9', "10ns":'10e-9', "5ns":'5e-9', "2.5ns":'2.5e-9'}
    self.acoplamiento = {"AC":'AC', "DC":'DC', "GND":'GND'}
    self.canal = {"1":'CH1', "2":'CH2'}
    self.atenuacion = {"1":'1', "10":'10'} 
    self.bytes_medida = {"2":'2', "1":'1'}
    self.medidas = {"frecuencia":'FREQ', "periodo":'PERI', "vmedio":'MEAN', "vpp":'PK2', "vrms":'CRM', "vmin":'MINI', "vmax":'MAXI', "tsubida":'RIS', "tbajada":'FALL'}
    self.canal_trigg = {"1":'CH1', "2":'CH2', "ext":'EXT', "ext5":'EXT5'}
    
    # Inicializamos el osciloscopio
    try:
      self.ins = usbtmc.Instrument("USB::" + id + "::INSTR")
    except ValueError:
      aviso = VentanaInfo("Parece que no hay ningun osciloscopio conectado. Por favor conectelo y asegurese de que esta encendido y reinicie la aplicacion.")

  def set_display(self, mode):
    '''Permite elegir entre modo de visualizacion XY o YT.
    
    Parametros:
      mode: string XY o YT, aunque si recibe cualquier otra cosa pondra el osciloscopio en modo YT.
    
    '''
    if mode == "XY":
      self.ins.write("DIS:FORM XY")
    else:
      self.ins.write("DIS:FORM YT")
  
  def set_horizontal(self, tiempo):
    '''Modifica la escala de tiempos del osciloscopio
    
    Parametros:
      tiempo: valor valido del diccionario sec_div.
    
    '''
    escala = self.sec_div[tiempo]
    self.ins.write("HOR:SCA " + escala)
  
  def set_trigger(self, channel, level):
    '''Configura el nivel y modo de disparo.
    
    Parametros:
      channel: valor valido del diccionario canal_trigg.
      level: nivel del disparo en voltios.
    
    '''
    ch = self.canal_trigg[channel]
    
    self.ins.write("TRIG:MAI:LEV " + str(level) + ";EDGE:SOU " + ch)
  
  def set_vertical(self, channel, v_d, coupling, probe):
    '''Modifica los ajustes de amplitud, acoplamiento y atenuacion de la sonda de los diferentes canales del osciloscopio.
    
    Parametros:
      channel: canal sobre el que se van a aplicar los cambios. Valor valido del diccionario canal.
      v_d: voltios/division que va a mostrar el canal. Valor valido del diccionario vol_div.
      coupling: Acoplamiento del canal. Valor valido del diccionario acoplamiento.
      probe: Atenuacion de la sonda conectada al canal. Valor valido del diccionario atenuacion.
    
    '''
    ch = self.canal[channel]
    vdiv = self.vol_div[v_d]
    acoplo = self.acoplamiento[coupling]
    att = self.atenuacion[probe]
    
    self.ins.write(ch + ":COUP " + acoplo + ";PRO " + probe + ";VOL " + vdiv)
  
  def get_data(self, source, start, stop, width):
    '''Obtiene los puntos que esta mostrando el osciloscopio por pantalla de un unico canal.
    
    Devuelve el valor en voltios de cada punto y el incremento de tiempo entre puntos en segundos.
    
    Se puede elegir el primer y ultimo punto que se quiere obtener siempre que esten entre el punto 1 y el 2500.
    La precision con la que se muestran los puntos es configurable y puede ser con uno o con dos bytes.
    
    Parametros:
      source: canal del que se quieren obtener los puntos. Valor valido del diccionario canal.
      start: primer punto de los que se quieren obtener. Tiene que ser mayor que uno y menor que 2500.
      stop: ultimo punto de los que se quieren obtener. Tiene que ser menor que 2500 y mayor que start. (Esto falta por cambiar)
      width: Precision de la medida, 1 o 2 bytes. Uno por defecto.
    
    '''
    intentos = 0
    while intentos < 8:
      try: # Es un manejo de la excepcion un poco largo, pero al haber varias llamadas parecidas puede fallar cualquiera y hay veces que no te das cuenta del fallo hasta el procesado de datos que hace al final
        codificacion = "RIB" #Entre 127 y -128 con un byte
        ch = self.canal[source]
        self.ins.write(ch + ":POS 0.0") # Lleva el canal al origen
        if start < 1:
          start = 1
        if stop > 2500:
          stop = 2500
        prec = self.bytes_medida[width]
        self.ins.write("DAT:ENC " + codificacion +";SOU " + ch + ";STAR " + str(start) + ";STOP " + str(stop) + ";WID " + prec)
        
        puntos_division = 250 #2500 puntos / 10 divisiones
        incremento_tiempo = float(self.ins.ask("HOR:MAI:SCA?")) / puntos_division
        v_div = float(self.ins.ask(ch + ":SCA?"))
        
        puntos = self.ins.ask_raw("CURV?")
        header_length = 2 + int(puntos[1]) #Calculamos el tamano de la cabecera para no cogerla
        puntos = puntos[header_length:-1]
        puntos = unpack('%sb' % len(puntos), puntos) #Los convertimos desde enteros con signo
        
        if prec == '2': #Si la resolucion no es dos la consideramos uno
          escala = 6553.4 #32767/5
        else:
          escala = 25.4 #127/5
        
        tension =[]
        for dato in puntos:
          dato = dato*v_div/escala
          tension.append(dato)
        return tension, incremento_tiempo
      
      except Exception as e:
        print('Excepcion')
        print e
        intentos += 1
      '''except usbtmc.usb.core.USBError:
        print 'USBError'
        get_data(source, start, stop, width)
      except ValueError:
        print 'ValueError'
        get_data(source, start, stop, width)
      except UnicodeDecodeError:
        print 'UnicodeError'
        get_data(source, start, stop, width)'''
  
  def disp_channel(self, state, channel):
    ''' Muestra u oculta los canales en el display del osciloscopio. 
    
    Parametros:
      state: Booleano, True es visible y False no visible.
      channel: canal sobre el que se van a aplicar los cambios. Valor valido del diccionario canal.
    
    '''
    ch = self.canal[channel]
    if(state == True):
      self.ins.write("SEL:" + ch + " ON")
    else:
      self.ins.write("SEL:" + ch + " OFF")
  
  def get_measure(self, channel, medida):
    ''' Obtiene las medidas del osciloscipio que estan disponibles en el menu Measure.
       
    Devuelve la medida con sus unidades y en formato ingenieril, es decir, con exponente multiplo de 3 desde pico hasta Tera.
    
    Parametros:
      channel: canal del que se quiere obtener la medida. Valor valido del diccionario canal.
      medida: Tipo de medida que se quiere realizar. Valor valido del diccionario medidas.
    
    '''
    # Los sleep despues de cada escritura son necesarios porque al osciloscopio no le da tiempo a configurarse tan rapido y devuelve un error
    ch = self.canal[channel]
    tipo_medida = self.medidas[medida]
    
    self.ins.write_raw("MEASU:IMM:SOU " + ch)
    time.sleep(0.5)
    self.ins.write_raw("MEASU:IMM:TYP " + tipo_medida)
    time.sleep(0.5)
    value = self.ins.ask_raw("MEASU:IMM:VAL?")
    value = self.formatter(value)
    units = self.ins.ask_raw("MEASU:IMM:UNI?")
    value = value + units[1:-2] #para quitar las comillas
    
    return value
  
  def formatter(self, value):
    ''' Cambia un numero de notacion cientifica a notacion ingenieril, desde pico hasta tera.
    Dependiendo del exponente asigna una letra para la magnitud de las unidades y multiplica por un valor de 1, 10 o 100 segun corresponda.
    
    Devuelve el numero con el nuevo formato.
    
    Parametros:
      value: numero en notacion cientifica al que se quiere cambiar el formato.
    
    '''
    # numero de decimales + punto
    prec = 3
    
    index = value.find('E')
    number = float(value[0:index])
    exp = value[index:-1]
    
    # Por si no esta definido luego
    new_exp = exp
    mult = 1
    
    if(exp == 'E-12'):
      mult = 1
      new_exp = 'p'
    if(exp == 'E-11'):
      mult = 10
      new_exp = 'p'
    if(exp == 'E-10'):
      mult == 100
      new_exp = 'p'
    if(exp == 'E-9'):
      mult = 1
      new_exp = 'n'
    if(exp == 'E-8'):
      mult = 10
      new_exp = 'n'
    if(exp == 'E-7'):
      mult = 100
      new_exp = 'n'
    if(exp == 'E-6'):
      mult = 1
      new_exp = 'u'
    if(exp == 'E-5'):
      mult = 10
      new_exp = 'u'
    if(exp == 'E-4'):
      mult = 100
      new_exp = 'u'
    if(exp == 'E-3'):
      mult = 1
      new_exp = 'm'
    if(exp == 'E-2'):
      mult = 10
      new_exp = 'm'
    if(exp == 'E-1'):
      mult = 100
      new_exp = 'm'
    if(exp == 'E0'):
      mult = 1
      new_exp = ''
    if(exp == 'E1'):
      mult = 10
      new_exp = ''
    if(exp == 'E2'):
      mult = 100
      new_exp = ''
    if(exp == 'E3'):
      mult = 1
      new_exp = 'K'
    if(exp == 'E4'):
      mult = 10
      new_exp = 'K'
    if(exp == 'E5'):
      mult = 100
      new_exp = 'K'
    if(exp == 'E6'):
      mult = 1
      new_exp = 'M'
    if(exp == 'E7'):
      mult = 10
      new_exp = 'M'
    if(exp == 'E8'):
      mult = 100
      new_exp = 'M'
    if(exp == 'E9'):
      mult = 1
      new_exp = 'G'
    if(exp == 'E10'):
      mult = 10
      new_exp = 'G'
    if(exp == 'E11'):
      mult = 100
      new_exp = 'G'
    if(exp == 'E12'):
      mult = 1
      new_exp = 'T'
    
    num = str(number * mult)
    dot = num.find('.')
    num = num[0:(dot+prec)]
    num = num + ' ' + new_exp
    if num == '9.9 E37':
      num = 'Err '
    return num
  
  def autoset(self, channel):
    ch = self.canal[channel]
    unidades = {'V':'', 'mV':'E-3'}
    
    self.ins.write(ch + ":POS 0.0")
    self.set_vertical(channel, '1v', "AC", "1")
    time.sleep(0.5)
    medida = self.get_measure(channel, 'vpp')
    a, b = medida.split(' ')
    a = str(float(a)/6)
    c = unidades[b]
    self.ins.write(ch + ":VOL " + a + c)


'''
def main(): 
  osc = Osciloscopio("0x0699::0x0369")
  osc.set_trigger('1', 3.5)
  osc.set_vertical("1", "2v", "AC", "1")
  osc.set_horizontal('250us')
  print osc.get_data("1", 1, 150, '1')
  

if __name__ == '__main__':
  main()
'''
