import sys
from PyQt4 import QtGui, QtCore
from Osciloscopio import *
#from Modbus import *
from Pines import *
import numpy as np
import time
import math
import pylab
from scipy.special import erfc
import logging

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter, MultipleLocator
from matplotlib.widgets import Cursor, Slider
from matplotlib.patches import Rectangle

class VentanaInfo(QtGui.QWidget):
  '''Tiene un boton aceptar para volver al orden de ejecucion'''
  
  def __init__(self, texto):
    '''Constructor de una ventana de informacion
    
    Parametros:
      texto: Texto que mostrar'a la ventana
    
    '''
    super(VentanaInfo, self).__init__()
    self.inicializa(texto)
  
  def inicializa(self, texto):
    win = QtGui.QMessageBox()
    win.timer = QtCore.QTimer(self)
    win.timer.timeout.connect(win.close)
    win.timer.start(10000) # Se cierra automaticamente a los 10 segundos
    win.setInformativeText(texto)
    win.setWindowTitle('Aviso')
    win.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/lab_master/img/icono.gif'))
    win.exec_()

class VentanaConfigIO(QtGui.QWidget):
  
  def __init__(self):
    super(VentanaConfigIO, self).__init__()
    
    grid = QtGui.QGridLayout()
    grid.setSpacing(5)
    
    tit_rate1 = QtGui.QLabel('Rate 1')
    tit_rate2 = QtGui.QLabel('Rate 2')
    tit_len1 = QtGui.QLabel('Length 1')
    tit_len2 = QtGui.QLabel('Length 2')
    tit_sync = QtGui.QLabel('Sync')
    
    tasas = ["10 Mbps","30 Mbps","70 Mbps","125 Mbps"]
    longitudes = ["4", "8", "12", "16"]
    
    combo_rate1 = QtGui.QComboBox(self)
    combo_rate2 = QtGui.QComboBox(self)
    combo_len1 = QtGui.QComboBox(self)
    combo_len2 = QtGui.QComboBox(self)
    combo_sync = QtGui.QComboBox(self)
    
    for t in tasas:
      combo_rate1.addItem(t)
      combo_rate2.addItem(t)
    
    for l in longitudes:
      combo_len1.addItem(l)
      combo_len2.addItem(l)
    
    combo_sync.addItem('sync 1')
    combo_sync.addItem('sync 2')
    combo_sync.addItem('SoF 1')
    combo_sync.addItem('SoF 2')
    
    bot_aceptar = QtGui.QPushButton('Aceptar', self)
    
    grid.addWidget(tit_rate1, 1, 1)
    grid.addWidget(combo_rate1, 1, 2)
    grid.addWidget(tit_len1, 1, 3)
    grid.addWidget(combo_len1, 1, 4)
    
    grid.addWidget(tit_rate2, 2, 1)
    grid.addWidget(combo_rate2, 2, 2)
    grid.addWidget(tit_len2, 2, 3)
    grid.addWidget(combo_len2, 2, 4)
    
    grid.addWidget(tit_sync, 3, 2)
    grid.addWidget(combo_sync, 3, 3)
    grid.addWidget(bot_aceptar, 3, 5)
    
    bot_aceptar.clicked.connect(lambda: self.aceptar(combo_rate1.currentText(), combo_rate2.currentText(), combo_len1.currentText(), combo_len2.currentText(), combo_sync.currentText()))
    
    self.setLayout(grid)
    self.setWindowTitle('Configuracion del generador')
    self.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/lab_master/img/icono.gif'))
    self.show()
    
  def aceptar(self, rate1, rate2, len1, len2, sync):
    length = {"4":0, "8":1, "12":2, "16":3}
    rate = {"10 Mbps":0, "30 Mbps":1, "70 Mbps":2, "125 Mbps":3}
    syn = {'sync 1':1, 'sync 2':2, 'SoF 1':3, 'SoF 2':4}
    
    pines = PinesFPGA()
    pines.setClock(syn[str(sync)])
    pines.setLength1(length[str(len1)])
    pines.setRate1(rate[str(rate1)])
    pines.setLength2(length[str(len2)])
    pines.setRate2(rate[str(rate2)])


class VentanaAviso(QtGui.QDialog):
  '''No tiene boton'''
  
  def __init__(self, texto):
    QtGui.QDialog.__init__(self)
    self.setModal(True)
    self.inicializa(texto)
  
  def inicializa(self, texto):
    grid = QtGui.QGridLayout()
    grid.setSpacing(5)
    
    aviso = QtGui.QLabel(texto)
    self.barra = QtGui.QProgressBar(self)
    self.barra.setMinimum(1)
    self.barra.setMaximum(64)

    grid.addWidget(aviso, 1, 1)
    grid.addWidget(self.barra, 2, 1)
    
    self.setLayout(grid) 
    self.setGeometry(200, 200, 200, 200)
    self.setWindowTitle('Aviso')
    self.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/lab_master/img/icono.gif'))
    
  def actualiza_barra(self, val):
    self.barra.setValue(val)

class VentanaPrincipal(QtGui.QWidget):
  global osc
  
  def __init__(self, osciloscopio):
    ''' Constructor de la ventana de inicio de la aplicacion.
    
    Parametros:
      osciloscopio: Objeto de la clase Osciloscopio
    
    '''
    
    super(VentanaPrincipal, self).__init__()
    self.osc = osciloscopio
    self.rellenaVentana()
  
  def rellenaVentana(self):
    
    grid = QtGui.QGridLayout()
    grid.setSpacing(5)
    
    tit_up = QtGui.QLabel('Uplink')
    tit_dw = QtGui.QLabel('Downlink')
    tit_tasa_u = QtGui.QLabel('Tasa binaria')
    tit_tasa_d = QtGui.QLabel('Tasa binaria')
    tit_long_u = QtGui.QLabel('Longitud de trama')
    tit_long_d = QtGui.QLabel('Longitud de trama')
    '''tit_lambda_u = QtGui.QLabel('Longitud de onda')
    tit_lambda_d = QtGui.QLabel('Longitud de onda')
    tit_enlace_u = QtGui.QLabel('Enlace')
    tit_enlace_d = QtGui.QLabel('Enlace')'''
    
    desp_tasa_u = QtGui.QComboBox(self)
    desp_tasa_d = QtGui.QComboBox(self)
    desp_long_u = QtGui.QComboBox(self)
    desp_long_d = QtGui.QComboBox(self)
    '''desp_lambda_u = QtGui.QComboBox(self)
    desp_lambda_d = QtGui.QComboBox(self)
    desp_enlace_u  = QtGui.QComboBox(self)
    desp_enlace_d  = QtGui.QComboBox(self)'''
    
    auto = QtGui.QCheckBox('Auto', self)
    
    tasas = ["10 Mbps","30 Mbps","70 Mbps","125 Mbps"]
    longitudes = ["4", "8", "12", "16"]
    lambdas = ["820","1300","1550"]
    enlaces = ["fibra", "latiguillo"]
    
    for t in tasas:
      desp_tasa_u.addItem(t)
      desp_tasa_d.addItem(t)
    for l in longitudes:
      desp_long_u.addItem(l)
      desp_long_d.addItem(l)
    '''for l in lambdas:
      desp_lambda_u.addItem(l)
      desp_lambda_d.addItem(l)
    for e in enlaces:
      desp_enlace_u.addItem(e)
      desp_enlace_d.addItem(e)'''
    
    bot_aceptar = QtGui.QPushButton('Aceptar', self)
    
    grid.addWidget(tit_up, 0, 1)
    grid.addWidget(tit_dw, 0, 4)
    grid.addWidget(tit_tasa_u, 2, 1)
    grid.addWidget(tit_tasa_d, 2, 4)
    grid.addWidget(tit_long_u, 3, 1)
    grid.addWidget(tit_long_d, 3, 4)
    #grid.addWidget(tit_lambda_u, 4, 1)
    #grid.addWidget(tit_lambda_d, 4, 4)
    grid.addWidget(desp_tasa_u, 2, 2)
    grid.addWidget(desp_tasa_d, 2, 5)
    grid.addWidget(desp_long_u, 3, 2)
    grid.addWidget(desp_long_d, 3, 5)
    '''grid.addWidget(desp_lambda_u, 4, 2)
    grid.addWidget(desp_lambda_d, 4, 5)
    
    grid.addWidget(tit_enlace_u, 5, 1)
    grid.addWidget(desp_enlace_u, 5, 2)
    grid.addWidget(tit_enlace_d, 5, 4)
    grid.addWidget(desp_enlace_d, 5, 5)'''
    
    grid.addWidget(bot_aceptar, 6, 3)
    grid.addWidget(auto, 6, 2)
    
    bot_aceptar.clicked.connect(lambda: self.aceptar(desp_tasa_u.currentText(), desp_long_u.currentText(), desp_tasa_d.currentText(), desp_long_d.currentText(), auto.isChecked()))
    
    self.setLayout(grid)
    self.setWindowTitle('FTTH')
    self.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/lab_master/img/icono.gif'))
    self.show()
    
  def aceptar(self, tasa_u, long_u, tasa_d, long_d, auto):
    # Diccionarios
    base_tiempos = {"10 Mbps":'50ns', "30 Mbps":'10ns', "70 Mbps":'5ns', "125 Mbps":'5ns'}
    length = {"4":0, "8":1, "12":2, "16":3}
    rate = {"125 Mbps":3, "70 Mbps":2, "30 Mbps":1, "10 Mbps":0}
    
    # Llamada a Pines o a Modbus
    '''pines = PinesFPGA()
    pines.setClock(0)
    pines.setLength1(length[str(long_u)])
    pines.setRate1(rate[str(tasa_u)])'''
    
    if auto:
      pines = PinesFPGA()
      pines.setClock(1)
      pines.setLength1(length[str(long_u)])
      pines.setRate1(rate[str(tasa_u)])
      self.osc.set_horizontal(base_tiempos[str(tasa_u)]) #Por los qstring de qt4
      #self.osc.set_vertical("1", amp1, "AC", "1")
      self.osc.autoset('1')
    
    # Configuramos el disparo
    self.osc.set_trigger('ext', 1)
    aviso = VentanaAviso('La adquisicion de datos puede tardar un tiempo.\nEspere, por favor.')
    aviso.show()
    lista_medidas1 = []
    
    # Toma 32 trazas del osciloscopio
    for i in range(32):
      aviso.actualiza_barra(i)
      QtCore.QCoreApplication.processEvents()
      medidas1 , inc_tiempo1 = self.osc.get_data('1', 500, 2000, '1')
      lista_medidas1.append(medidas1)
    
    if auto:
      pines.setClock(2)
      pines.setLength2(length[str(long_d)])
      pines.setRate2(rate[str(tasa_d)])
      self.osc.set_horizontal(base_tiempos[str(tasa_d)]) #Por los qstring de qt4
      #self.osc.set_vertical("2", amp2, "AC", "1")
      self.osc.autoset('2')
      
    
    '''# Llamada a Pines o a Modbus
    pines.setClock(1)
    pines.setLength2(length[str(long_d)])
    pines.setRate2(rate[str(tasa_d)])'''
    
    lista_medidas2 = []
    # Toma 32 trazas del osciloscopio
    for i in range(32):
      aviso.actualiza_barra(i+32)
      QtCore.QCoreApplication.processEvents()
      medidas2 , inc_tiempo2 = self.osc.get_data('2', 500, 2000, '1')
      lista_medidas2.append(medidas2)
    
    self.ojo = DisplayOjo(lista_medidas1, inc_tiempo1, lista_medidas2, inc_tiempo2)
    self.ojo.show()
    
    # Quitamos el disiparo externo
    self.osc.set_trigger('1', 0)
    
    #Quitamos los pines
    #pines.quitGPIO()
    

class DisplayOjo(QtGui.QWidget):
  
  def __init__(self, medidas1, tiempo1, medidas2, tiempo2):
    super(DisplayOjo, self).__init__()
    
    logging.basicConfig(level=logging.DEBUG) # Trazas para comprobar el correcto funcionamiento
    self.setWindowTitle('Diagrama de ojo')
    self.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/lab_master/img/icono.gif'))
    self.setFixedSize(900,700)
    tab_widget = QtGui.QTabWidget()
    tab1 = QtGui.QWidget()
    tab2 = QtGui.QWidget()
    
    p1 = QtGui.QVBoxLayout(tab1)
    p2 = QtGui.QVBoxLayout(tab2)
    
    tab_widget.addTab(tab1, "820 nm")
    tab_widget.addTab(tab2, "1300 nm")
    
    vbox = QtGui.QVBoxLayout()
    vbox.addWidget(tab_widget)
    
    # Hacemos las medidas disponibles a todo el objeto
    self.lista_medidas_t1 = medidas1
    self.lista_medidas_t2 = medidas2
    self.inc_tiempo_t1 = tiempo1
    self.inc_tiempo_t2 = tiempo2
    
    self.creaInterfaz(p1, p2)
    
    self.setLayout(vbox)
  
  def creaInterfaz(self, p1, p2):
    
    self.figure_t1 = plt.figure(1)
    self.canvas_t1 = FigureCanvas(self.figure_t1)
    self.canvas_t1.setParent(self)
    
    self.figure_t2 = plt.figure(2)
    self.canvas_t2 = FigureCanvas(self.figure_t2)
    self.canvas_t2.setParent(self)
    
    # Creamos los plots
    plt.figure(1)
    self.ax1_t1 = plt.subplot2grid((2,2),(0,0), colspan=2) #Diagrama de ojo
    self.ax2_t1 = plt.subplot2grid((2,2),(1,0))            #Histogramas
    self.ax3_t1 = plt.subplot2grid((2,2),(1,1))            #erfc
    plt.subplots_adjust(left=0.15, right=0.85, bottom=0.1, top=0.9, hspace=0.25)
    
    plt.figure(2)
    self.ax1_t2 = plt.subplot2grid((2,2),(0,0), colspan=2) #Diagrama de ojo
    self.ax2_t2 = plt.subplot2grid((2,2),(1,0))            #Histogramas
    self.ax3_t2 = plt.subplot2grid((2,2),(1,1))            #erfc
    plt.subplots_adjust(left=0.15, right=0.85, bottom=0.1, top=0.9, hspace=0.25)
    
    # Creamos los formatos que van a mostrar las unidades que se pintan
    formatter_tiempo = EngFormatter(unit='s', places=1)
    formatter_amp = EngFormatter(unit='v', places=1)
    self.lista_tiempo_t1 = []
    self.lista_tiempo_t2 = []
    
    # Sabemos la diferencia de tiempos entre medidas, asi que multiplicando la posicion
    # de cada dato por el incremento de tiempo sabemos su posicion en el eje X
    for i in range(len(self.lista_medidas_t1[1])):
      self.lista_tiempo_t1.append(self.inc_tiempo_t1*i)
    for i in range(len(self.lista_medidas_t2[1])):
      self.lista_tiempo_t2.append(self.inc_tiempo_t2*i)
    
    
    # Representamos el diagrama
    plt.figure(1)
    self.ax1_t1.hold(True)
    for i in range(len(self.lista_medidas_t1)):
      self.ax1_t1.plot(self.lista_tiempo_t1, self.lista_medidas_t1[i], '#0b610b')
    self.ax1_t1.hold(False)
    self.ax1_t1.set_xlabel('tiempo')
    self.ax1_t1.set_ylabel('amplitud')
    self.ax1_t1.xaxis.set_major_formatter(formatter_tiempo)
    self.ax1_t1.yaxis.set_major_formatter(formatter_amp)
    self.ax1_t1.xaxis.set_minor_locator(MultipleLocator(self.inc_tiempo_t1 * 25))
    self.ax1_t1.yaxis.set_minor_locator(MultipleLocator(0.5))
    
    plt.figure(2)
    self.ax1_t2.hold(True)
    for i in range(len(self.lista_medidas_t2)):
      self.ax1_t2.plot(self.lista_tiempo_t2, self.lista_medidas_t2[i], '#0b610b')
    self.ax1_t2.hold(False)
    self.ax1_t2.set_xlabel('tiempo')
    self.ax1_t2.set_ylabel('amplitud')
    self.ax1_t2.xaxis.set_major_formatter(formatter_tiempo)
    self.ax1_t2.yaxis.set_major_formatter(formatter_amp)
    self.ax1_t2.xaxis.set_minor_locator(MultipleLocator(self.inc_tiempo_t2 * 25))
    self.ax1_t2.yaxis.set_minor_locator(MultipleLocator(0.5))
    
    # Creamos las barras de muestreo y umbral
    plt.figure(1)
    self.intervalo_amplitud_t1 = self.ax1_t1.yaxis.get_data_interval()
    umbralInit_t1 = (self.intervalo_amplitud_t1[0]+self.intervalo_amplitud_t1[1])/2
    muestreoInit_t1 = self.lista_tiempo_t1[len(self.lista_tiempo_t1)-1]/2
    
    plt.figure(2)
    self.intervalo_amplitud_t2 = self.ax1_t2.yaxis.get_data_interval()
    umbralInit_t2 = (self.intervalo_amplitud_t2[0]+self.intervalo_amplitud_t2[1])/2
    muestreoInit_t2 = self.lista_tiempo_t2[len(self.lista_tiempo_t2)-1]/2
    
    # Pintamos la erfc
    eje_x = np.arange(0, 10, 0.5)
    plt.figure(1)
    self.ax3_t1.semilogy(eje_x, 0.5*erfc(eje_x/math.sqrt(2)), color='#08088a')
    plt.figure(2)
    self.ax3_t2.semilogy(eje_x, 0.5*erfc(eje_x/math.sqrt(2)), color='#08088a')
    
    logging.debug('se crea el eje semilogaritmico')
    
    plt.figure(1)
    self.ax3_t1.set_xlabel('q')
    self.ax3_t1.set_ylabel('BER')
    plt.figure(2)
    self.ax3_t2.set_xlabel('q')
    self.ax3_t2.set_ylabel('BER')
    
    # Creamos las barras horizontales y verticales de los subplots
    plt.figure(1)
    self.var_t1 = 25*self.inc_tiempo_t1
    self.barMuestreo_t1 = self.ax1_t1.axvline(x=muestreoInit_t1, color='blue')
    self.barMuestreoMas_t1 = self.ax1_t1.axvline(x=muestreoInit_t1 + self.var_t1, color='blue', linestyle='--')
    self.barMuestreoMenos_t1 = self.ax1_t1.axvline(x=muestreoInit_t1 - self.var_t1, color='blue', linestyle='--')
    self.barUmbral_t1 = self.ax1_t1.axhline(y=umbralInit_t1, color='green')
    self.barDecision2_t1 = self.ax2_t1.axvline(x=umbralInit_t1, color='green')
    self.bar_q_t1 = self.ax3_t1.axvline(x=10, color='blue', linestyle='--') # Valor distinto de cero para el logaritmo
    self.bar_ber_t1 = self.ax3_t1.axhline(y=10, color='blue', linestyle='--')
    
    plt.figure(2)
    self.var_t2 = 25*self.inc_tiempo_t2
    self.barMuestreo_t2 = self.ax1_t2.axvline(x=muestreoInit_t2, color='blue')
    self.barMuestreoMas_t2 = self.ax1_t2.axvline(x=muestreoInit_t2 + self.var_t2, color='blue', linestyle='--')
    self.barMuestreoMenos_t2 = self.ax1_t2.axvline(x=muestreoInit_t2 - self.var_t2, color='blue', linestyle='--')
    self.barUmbral_t2 = self.ax1_t2.axhline(y=umbralInit_t2, color='green')
    self.barDecision2_t2 = self.ax2_t2.axvline(x=umbralInit_t2, color='green')
    self.bar_q_t2 = self.ax3_t2.axvline(x=10, color='blue', linestyle='--') # Valor distinto de cero para el logaritmo
    self.bar_ber_t2 = self.ax3_t2.axhline(y=10, color='blue', linestyle='--')
    
    # Esto hay que hacerlo antes de dibujar para que pueda poner los valores medios, q y la ber
    self.resultados_label_t1 = QtGui.QLabel(self)
    self.resultados_label_t2 = QtGui.QLabel(self)
    
    # Pintamos el resto de subplots
    self.dibuja_t1(muestreoInit_t1, umbralInit_t1)
    self.dibuja_t2(muestreoInit_t2, umbralInit_t2)
    
    # Barra de herramientas de matplotlib
    plt.figure(1)
    self.mpl_toolbar_t1 = NavigationToolbar(self.canvas_t1, self)
    plt.figure(2)
    self.mpl_toolbar_t2 = NavigationToolbar(self.canvas_t2, self)
    
    self.box1_t1 = QtGui.QLineEdit(self)
    self.box2_t1 = QtGui.QLineEdit(self)
    self.box1_t1.setText("50")
    self.box2_t1.setText("50")
    self.muestreo_label_t1 = QtGui.QLabel('Punto de muestreo', self)
    self.umbral_label_t1 = QtGui.QLabel('Umbral', self)
    
    self.boton_t1 = QtGui.QPushButton("Pintar", self)
    self.connect(self.boton_t1, QtCore.SIGNAL('clicked()'), self.botonClick_t1)
    
    self.box1_t2 = QtGui.QLineEdit(self)
    self.box2_t2 = QtGui.QLineEdit(self)
    self.box1_t2.setText("50")
    self.box2_t2.setText("50")
    self.muestreo_label_t2 = QtGui.QLabel('Punto de muestreo', self)
    self.umbral_label_t2 = QtGui.QLabel('Umbral', self)
    
    self.boton_t2 = QtGui.QPushButton("Pintar", self)
    self.connect(self.boton_t2, QtCore.SIGNAL('clicked()'), self.botonClick_t2)
    
    hbox_t1 = QtGui.QHBoxLayout()
    hbox_t2 = QtGui.QHBoxLayout()
    
    for w in [self.muestreo_label_t1, self.box1_t1, self.umbral_label_t1, self.box2_t1, self.boton_t1]:
      hbox_t1.addWidget(w)
      hbox_t1.setAlignment(w, QtCore.Qt.AlignVCenter)
    
    for w in [self.muestreo_label_t2, self.box1_t2, self.umbral_label_t2, self.box2_t2, self.boton_t2]:
      hbox_t2.addWidget(w)
      hbox_t2.setAlignment(w, QtCore.Qt.AlignVCenter)
    
    p1.addWidget(self.canvas_t1)
    p1.addWidget(self.mpl_toolbar_t1)
    p1.addWidget(self.resultados_label_t1)
    p1.addLayout(hbox_t1)
    
    p2.addWidget(self.canvas_t2)
    p2.addWidget(self.mpl_toolbar_t2)
    p2.addWidget(self.resultados_label_t2)
    p2.addLayout(hbox_t2)
  
  def botonClick_t1(self):
    
    logging.debug('entramos en la rutina botonclick de la primera pestana')
    muestreo = int(self.box1_t1.text()) # Cogemos los valores de los porcentajes como enteros de las cajas de texto
    umbral = int(self.box2_t1.text())
    
    if muestreo > 100: # Nos aseguramos de que estan entre cero y cien
      muestreo = 100
    if muestreo < 0:
      muestreo = 0
    muestreo = muestreo/100.0 # Los ponemos en tanto por uno y los convertimos a decimales
    
    if umbral > 100: # Nos aseguramos de que estan entre cero y cien
      umbral = 100
    if umbral < 0:
      umbral = 0
    umbral = umbral/100.0 # Los ponemos en tanto por uno y los convertimos a decimales
    
    # Calculamos con que valores corresponden los porcentajes
    valMuestreo = (muestreo*self.lista_tiempo_t1[len(self.lista_tiempo_t1)-1])
    valUmbral = ((self.intervalo_amplitud_t1[1] - self.intervalo_amplitud_t1[0]) * umbral) + self.intervalo_amplitud_t1[0]
    logging.debug('muestreo %s umbral %s', str(valMuestreo), str(valUmbral))    
    self.dibuja_t1(valMuestreo, valUmbral)
  
  def botonClick_t2(self):
    
    logging.debug('entramos en la rutina botonclick de la segunda pestana')
    muestreo = int(self.box1_t2.text()) # Cogemos los valores de los porcentajes como enteros de las cajas de texto
    umbral = int(self.box2_t2.text())
    
    if muestreo > 100: # Nos aseguramos de que estan entre cero y cien
      muestreo = 100
    if muestreo < 0:
      muestreo = 0
    muestreo = muestreo/100.0 # Los ponemos en tanto por uno y los convertimos a decimales
    
    if umbral > 100: # Nos aseguramos de que estan entre cero y cien
      umbral = 100
    if umbral < 0:
      umbral = 0
    umbral = umbral/100.0 # Los ponemos en tanto por uno y los convertimos a decimales
    
    # Calculamos con que valores corresponden los porcentajes
    valMuestreo = (muestreo*self.lista_tiempo_t2[len(self.lista_tiempo_t2)-1])
    valUmbral = ((self.intervalo_amplitud_t2[1] - self.intervalo_amplitud_t2[0]) * umbral) + self.intervalo_amplitud_t2[0]
    logging.debug('muestreo %s umbral %s', str(valMuestreo), str(valUmbral))    
    self.dibuja_t2(valMuestreo, valUmbral)
  
  def dibuja_t1(self, muestreo, umbral):
    plt.figure(1)
    logging.debug('entramos en dibuja')
    puntoMuestreo = int(muestreo/self.inc_tiempo_t1)
    amp = []
    
    for i in range(len(self.lista_medidas_t1)): # Guardamos los puntos entre mas y menos 25 posiciones del punto de muestreo de todas las tramas guardadas
      for j in range(-25, 25):
        try:
          amp.append(self.lista_medidas_t1[i][puntoMuestreo + j])
        except IndexError:
          logging.debug('oob')
    
    # Discriminamos segun el umbral
    val0 = []
    val1 = []
    
    for i in range(len(amp)):
      if(amp[i] < umbral):
        val0.append(amp[i])
      else:
        val1.append(amp[i])
    
    # Pintamos los histogramas y las gaussianas
    self.ax2_t1.cla()
    self.ax2_t1.set_xlabel('amplitud')
    norm0, bins, patches = self.ax2_t1.hist(val0, bins=200,range=[(5/4)*self.intervalo_amplitud_t1[0], (5/4)*self.intervalo_amplitud_t1[1]], normed=True, histtype='step', color='#8181f7', rwidth=100)
    
    norm1, bins, patches = self.ax2_t1.hist(val1, bins=200,range=[(5/4)*self.intervalo_amplitud_t1[0], (5/4)*self.intervalo_amplitud_t1[1]], normed=True, histtype='step', color='#fa5858', rwidth=100)
    
    v0, sigma0 = self.media_y_varianza(val0)
    gauss0 = pylab.normpdf(bins, v0, sigma0)
    self.ax2_t1.plot(bins, gauss0, linewidth=2, color='#0404b4')#azul
    
    v1, sigma1 = self.media_y_varianza(val1)
    gauss1 = pylab.normpdf(bins, v1, sigma1)
    self.ax2_t1.plot(bins, gauss1, linewidth=2, color='#b40404')#rojo
    
    # Calculamos la ber
    q = math.fabs(v1-v0)/(sigma1+sigma0)
    ber = 0.5*erfc(q/math.sqrt(2))
    
    self.muestra_resultados_t1(v0, sigma0, v1, sigma1, q, ber, len(val0), len(val1))
    
    # Recolocamos todas las barras
    self.ax2_t1.add_line(self.barDecision2_t1) # Vuelve a pintar la barra del umbral cuando se redibuja
    self.ax3_t1.add_line(self.bar_q_t1)
    self.ax3_t1.add_line(self.bar_ber_t1)
    self.barMuestreo_t1.set_xdata(muestreo)
    self.barMuestreoMas_t1.set_xdata(muestreo + self.var_t1)
    self.barMuestreoMenos_t1.set_xdata(muestreo - self.var_t1)
    self.barUmbral_t1.set_ydata(umbral)
    self.barDecision2_t1.set_xdata(umbral)
    logging.debug('colocamos las barras en ax3')
    self.bar_q_t1.set_xdata(q)
    self.bar_ber_t1.set_ydata(ber)
    logging.debug('colocadas')
    
    self.canvas_t1.draw()
    logging.debug('ya se ha redibujado')
  
  def dibuja_t2(self, muestreo, umbral):
    logging.debug('entramos en dibuja')
    plt.figure(2)
    puntoMuestreo = int(muestreo/self.inc_tiempo_t2)
    amp = []
    
    for i in range(len(self.lista_medidas_t2)): # Guardamos los puntos entre mas y menos 25 posiciones del punto de muestreo de todas las tramas guardadas
      for j in range(-25, 25):
        try:
          amp.append(self.lista_medidas_t2[i][puntoMuestreo + j])
        except IndexError:
          logging.debug('oob')
    
    # Discriminamos segun el umbral
    val0 = []
    val1 = []
    
    for i in range(len(amp)):
      if(amp[i] < umbral):
        val0.append(amp[i])
      else:
        val1.append(amp[i])
    
    # Pintamos los histogramas y las gaussianas
    self.ax2_t2.cla()
    self.ax2_t2.set_xlabel('amplitud')
    norm0, bins, patches = self.ax2_t2.hist(val0, bins=200,range=[(5/4)*self.intervalo_amplitud_t2[0], (5/4)*self.intervalo_amplitud_t2[1]], normed=True, histtype='step', color='#8181f7', rwidth=100)
    
    norm1, bins, patches = self.ax2_t2.hist(val1, bins=200,range=[(5/4)*self.intervalo_amplitud_t2[0], (5/4)*self.intervalo_amplitud_t2[1]], normed=True, histtype='step', color='#fa5858', rwidth=100)
    
    v0, sigma0 = self.media_y_varianza(val0)
    gauss0 = pylab.normpdf(bins, v0, sigma0)
    self.ax2_t2.plot(bins, gauss0, linewidth=2, color='#0404b4')#azul
    
    v1, sigma1 = self.media_y_varianza(val1)
    gauss1 = pylab.normpdf(bins, v1, sigma1)
    self.ax2_t2.plot(bins, gauss1, linewidth=2, color='#b40404')#rojo
    
    # Calculamos la ber
    q = math.fabs(v1-v0)/(sigma1+sigma0)
    ber = 0.5*erfc(q/math.sqrt(2))
    
    self.muestra_resultados_t2(v0, sigma0, v1, sigma1, q, ber, len(val0), len(val1))
    
    # Recolocamos todas las barras
    self.ax2_t2.add_line(self.barDecision2_t2) # Vuelve a pintar la barra del umbral cuando se redibuja
    self.ax3_t2.add_line(self.bar_q_t2)
    self.ax3_t2.add_line(self.bar_ber_t2)
    self.barMuestreo_t2.set_xdata(muestreo)
    self.barMuestreoMas_t2.set_xdata(muestreo + self.var_t2)
    self.barMuestreoMenos_t2.set_xdata(muestreo - self.var_t2)
    self.barUmbral_t2.set_ydata(umbral)
    self.barDecision2_t2.set_xdata(umbral)
    logging.debug('colocamos las barras en ax3')
    self.bar_q_t2.set_xdata(q)
    self.bar_ber_t2.set_ydata(ber)
    logging.debug('colocadas')
    
    self.canvas_t2.draw()
    logging.debug('ya se ha redibujado')
  
  def muestra_resultados_t1(self, v0, sigma0, v1, sigma1, q, ber, num0, num1):
    string = 'v0: ' + str(round(v0,3)) + '\tsigma0: ' + str(round(sigma0,3)) + '\tnumero de muestras0: ' + str(num0) + '\tQ: ' + str(round(q,2)) + '\n\n' + 'v1: ' + str(round(v1,3)) + '\tsigma1: ' + str(round(sigma1,3)) + '\tnumero de muestras1: ' + str(num1) + '\tBER: ' + '%.2e' % ber # se muestra la ber en notacion cientifica
    plt.figure(1)
    self.resultados_label_t1.setText(string)
  
  def muestra_resultados_t2(self, v0, sigma0, v1, sigma1, q, ber, num0, num1):
    string = 'v0: ' + str(round(v0,3)) + '\tsigma0: ' + str(round(sigma0,3)) + '\tnumero de muestras0: ' + str(num0) + '\tQ: ' + str(round(q,2)) + '\n\n' + 'v1: ' + str(round(v1,3)) + '\tsigma1: ' + str(round(sigma1,3)) + '\tnumero de muestras1: ' + str(num1) + '\tBER: ' + '%.2e' % ber # se muestra la ber en notacion cientifica
    plt.figure(2)
    self.resultados_label_t2.setText(string)
  
  def media_y_varianza(self, data): 
    media = 0.0
    var = 0.0
    n = len(data)
    for i in range(n):
      media = media + data[i]
    media = media/n
    for i in range(n):
      var = var + math.pow(media - data[i], 2)
    var = math.sqrt(var / (n-1))
    return media, var
  
class VentanaConfiguracion(QtGui.QWidget):
  global osc
    
  def __init__(self, osciloscopio):
    '''Constructor de la ventana de configuracion del osciloscopio.
    
    Parametros:
      osciloscopio: Objeto de la clase Osciloscopio
    
    '''
    #Inicializacion de la ventana y de la variable osciloscopio con el objeto osciloscopio pasado como parametro
    super(VentanaConfiguracion, self).__init__()
    self.osc = osciloscopio
    self.conf_osc()
  
  def conf_osc(self):
    '''Anade funcionalidades a la ventana de configuracion del osciloscopio.
    
    '''
    #Se crean los elementos de la ventana y se les anaden funcionalidades
    grid = QtGui.QGridLayout()
    grid.setSpacing(5)
    
    bot_aceptar = QtGui.QPushButton('Configurar', self)
    bot_cerrar = QtGui.QPushButton('Cerrar', self)
    
    tit_tiempo = QtGui.QLabel('Base de\ntiempos')
    tit_display = QtGui.QLabel('Modo del display')
    tit_vdiv1 = QtGui.QLabel('V/div')
    tit_acop1 = QtGui.QLabel('Coupling')
    tit_att1 = QtGui.QLabel('Atenuacion de\nla sonda')
    tit_vdiv2 = QtGui.QLabel('V/div')
    tit_acop2 = QtGui.QLabel('Coupling')
    tit_att2 = QtGui.QLabel('Atenuacion de\nla sonda')
    tit_ojo = QtGui.QLabel('Diagrama\nde ojo')
    tit_tbit = QtGui.QLabel('Tiempo de\nbit')
    
    ch1 = QtGui.QCheckBox('Ch 1', self)
    ch2 = QtGui.QCheckBox('Ch 2', self)
    
    desp_tiempo = QtGui.QComboBox(self)
    desp_tiempo.addItem("100ms")
    desp_tiempo.addItem("100ns")
    desp_tiempo.addItem("100us")
    desp_tiempo.addItem("10ms")
    desp_tiempo.addItem("10ns")
    desp_tiempo.addItem("10s")
    desp_tiempo.addItem("10us")
    desp_tiempo.addItem("1ms")
    desp_tiempo.addItem("1s")
    desp_tiempo.addItem("1us")
    desp_tiempo.addItem("2.5ms")
    desp_tiempo.addItem("2.5ns")
    desp_tiempo.addItem("2.5s")
    desp_tiempo.addItem("2.5us")
    desp_tiempo.addItem("250ms")
    desp_tiempo.addItem("250ns")
    desp_tiempo.addItem("250us")
    desp_tiempo.addItem("25ms")
    desp_tiempo.addItem("25ns")
    desp_tiempo.addItem("25s")
    desp_tiempo.addItem("25us")
    desp_tiempo.addItem("500ms")
    desp_tiempo.addItem("500ns")
    desp_tiempo.addItem("500us")
    desp_tiempo.addItem("50ms")
    desp_tiempo.addItem("50ns")
    desp_tiempo.addItem("50s")
    desp_tiempo.addItem("50us")
    desp_tiempo.addItem("5ms")
    desp_tiempo.addItem("5ns")
    desp_tiempo.addItem("5s")
    desp_tiempo.addItem("5us")
    
    desp_disp = QtGui.QComboBox(self)
    desp_disp.addItem("YT")
    desp_disp.addItem("XY")
    
    desp_vdiv1 = QtGui.QComboBox(self)
    desp_vdiv1.addItem("100mv")
    desp_vdiv1.addItem("10mv")
    desp_vdiv1.addItem("1v")
    desp_vdiv1.addItem("200mv")
    desp_vdiv1.addItem("20mv")
    desp_vdiv1.addItem("2mv")
    desp_vdiv1.addItem("2v")
    desp_vdiv1.addItem("500mv")
    desp_vdiv1.addItem("50mv")
    desp_vdiv1.addItem("5mv")
    desp_vdiv1.addItem("5v")
    
    desp_vdiv2 = QtGui.QComboBox(self)
    desp_vdiv2.addItem("100mv")
    desp_vdiv2.addItem("10mv")
    desp_vdiv2.addItem("1v")
    desp_vdiv2.addItem("200mv")
    desp_vdiv2.addItem("20mv")
    desp_vdiv2.addItem("2mv")
    desp_vdiv2.addItem("2v")
    desp_vdiv2.addItem("500mv")
    desp_vdiv2.addItem("50mv")
    desp_vdiv2.addItem("5mv")
    desp_vdiv2.addItem("5v")
    
    desp_acop1 = QtGui.QComboBox(self)
    desp_acop1.addItem("AC")
    desp_acop1.addItem("DC")
    desp_acop1.addItem("GND")
        
    desp_acop2 = QtGui.QComboBox(self)
    desp_acop2.addItem("AC")
    desp_acop2.addItem("DC")
    desp_acop2.addItem("GND")
        
    desp_att1 = QtGui.QComboBox(self)
    desp_att1.addItem("x1")
    desp_att1.addItem("x10")
    
    desp_att2 = QtGui.QComboBox(self)
    desp_att2.addItem("x1")
    desp_att2.addItem("x10")
    
    #grid.addWidget(widget, r, c, [num_r, num_c])
    grid.addWidget(ch1, 1, 0)
    grid.addWidget(tit_vdiv1, 1, 1)
    grid.addWidget(desp_vdiv1, 1, 2)
    grid.addWidget(tit_acop1, 1, 3)
    grid.addWidget(desp_acop1, 1, 4)
    grid.addWidget(tit_att1, 1, 5)
    grid.addWidget(desp_att1, 1, 6)
    
    grid.addWidget(ch2, 2, 0)
    grid.addWidget(tit_vdiv2, 2, 1)
    grid.addWidget(desp_vdiv2, 2, 2)
    grid.addWidget(tit_acop2, 2, 3)
    grid.addWidget(desp_acop2, 2, 4)
    grid.addWidget(tit_att2, 2, 5)
    grid.addWidget(desp_att2, 2, 6)
    
    grid.addWidget(tit_tiempo, 3, 1)
    grid.addWidget(desp_tiempo, 3, 2)
    grid.addWidget(tit_display, 3, 4)
    grid.addWidget(desp_disp, 3, 5)
    
    grid.addWidget(bot_aceptar, 4, 4)
    grid.addWidget(bot_cerrar, 8, 5)
    
    bot_cerrar.clicked.connect(self.close)
    bot_aceptar.clicked.connect(lambda: self.aceptar_conf(desp_tiempo.currentText(), desp_disp.currentText(), ch1.isChecked(), desp_vdiv1.currentText(), desp_acop1.currentText(), desp_att1.currentText(), ch2.isChecked(), desp_vdiv2.currentText(), desp_acop2.currentText(), desp_att2.currentText()))
    self.setLayout(grid)
        
    self.setGeometry(100, 100, 500, 500)
    self.setWindowTitle('Control Osciloscopio')
    self.setWindowIcon(QtGui.QIcon('/home/debian/Desktop/TFG/img/icono.gif'))
    self.show()
  
  def aceptar_conf(self, t, display, ch1, vdiv1, acop1, att1, ch2, vdiv2, acop2, att2):
    '''Configura el osciloscopio con los valores que se han seleccionado en la ventana.
    
    Parametros:
      t: Base de tiempos del osciloscopio
      display: Modo del display (XY o YT).
      ch1: Muestra o no el canal uno.
      vdiv1: Escala vertical del canal uno.
      acop1: Acoplamiento del canal uno.
      att1: Atenuacion de la sonda del canal uno.
      ch2: Muestra o no el canal dos.
      vdiv2: Escala vertical del canal dos.
      acop2: Acoplamiento del canal dos.
      att2: Atenuacion de la sonda del canal dos.
    
    '''
    #Cuando se acepta, se envian las configuraciones al osciloscopio que se ha pasado como parametro
    self.osc.set_display(display)
    self.osc.set_horizontal(str(t))
    if(ch1):
      self.osc.disp_channel(True, '1')
      self.osc.set_vertical('1', str(vdiv1), str(acop1), str(att1).strip('x'))
    else:
      self.osc.disp_channel(False, '1')
    
    if(ch2):
      self.osc.disp_channel(True, '2')
      self.osc.set_vertical('2', str(vdiv2), str(acop2), str(att2).strip('x'))
    else:
      self.osc.disp_channel(False, '2')
