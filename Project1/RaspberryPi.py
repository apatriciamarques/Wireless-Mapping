#Trabalho 1 - Aquisição de dados e comunicação

import PyQt5
from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
from pyqtgraph.Qt import QtCore, QtGui
import os
import serial
import numpy as np
import sys

#FRONTEND

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

        #janela pyqtgraph, onde coloca os valores recebidos do Arduino
        #num gráfico xy (plot)
        hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]

        # plot data: x, y values
        self.graphWidget.plot(hour, temperature)

def button1_clicked():
   print("Button 1 clicked")

def button2_clicked():
   print("Button 2 clicked") 

def button3_clicked():
   print("Button 3 clicked")   

def main():

    app = QApplication(sys.argv)
    main = MainWindow()

    button1 = QPushButton(main)
    button1.setText("Start")
    button1.move(64,32)
    button1.clicked.connect(button1_clicked)

    button2 = QPushButton(main)
    button2.setText("Stop")
    button2.move(64,64)
    button2.clicked.connect(button2_clicked)

    button3 = QPushButton(main)
    button3.setText("Comando")
    button3.move(64,96)
    button3.clicked.connect(button3_clicked)

    main.setGeometry(50,50,320,200)
    main.setWindowTitle("IAD")
    main.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


#BACKEND

import serial
import time

# USB_PORT = "/dev/ttyUSB0"  # Arduino Uno R3 Compatible
USB_PORT = "/dev/ttyACM0"  # Arduino Uno WiFi Rev2

# Imports
import serial

try:
   ser = serial.Serial(USB_PORT, 9600, timeout=2)
except:
   print("ERROR - Could not open USB serial port.  Please check your port name and permissions.")
   print("Exiting program.")
   exit()

# Read and record the data
data =[]                       # empty list to store the data
for i in range(50):
    b = ser.readline()         # read a byte string
        string_n = b.decode()  # decode byte string into Unicode  
    string = string_n.rstrip() # remove \n and \r
    flt = float(string)        # convert string to float
    print(flt)
    data.append(flt)           # add to the end of data list
    time.sleep(0.1)            # wait (sleep) 0.1 seconds

ser.close()

import matplotlib.pyplot as plt
# if using a Jupyter notebook include
%matplotlib inline

plt.plot(data)
plt.xlabel('Time (seconds)')
plt.ylabel('Potentiometer Reading')
plt.title('Potentiometer Reading vs. Time')
plt.show()