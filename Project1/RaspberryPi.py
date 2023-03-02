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


# Envia, a intervalos definidos, um comando ao Arduíno
# para que este adquira um valor analógico e o envie
# Imprime esse valor, e actualiza o plot

# USB_PORT = "/dev/ttyUSB0"  # Arduino Uno R3 Compatible
USB_PORT = "/dev/ttyACM0"  # Arduino Uno WiFi Rev2

# Imports
import serial

# Functions
def print_commands():
   """Prints available commands."""
   print("Available commands:")
   print("  a - Retrieve Arduino value")
   print("  l - Turn on Arduino LED")
   print("  k - Turn off Arduino LED")
   print("  x - Exit program")

# Main
# Connect to USB serial port at 9600 baud
try:
   usb = serial.Serial(USB_PORT, 9600, timeout=2)
except:
   print("ERROR - Could not open USB serial port.  Please check your port name and permissions.")
   print("Exiting program.")
   exit()
# Send commands to Arduino
print("Enter a command from the keyboard to send to the Arduino.")
print_commands()
while True:
   command = input("Enter command: ")
   if command == "a":  # read Arduino A0 pin value
      usb.write(b'read_a0')  # send command to Arduino
      line = usb.readline()  # read input from Arduino
      line = line.decode()  # convert type from bytes to string
      line = line.strip()  # strip extra whitespace characters
      if line.isdigit():  # check if line contains only digits
         value = int(line)  # convert type from string to int
      else:
         print("Unknown value '" + line + "', setting to 0.")
         value = 0
      print("Arduino A0 value:", value)
   elif command == "l":  # turn on Arduino LED
      usb.write(b'led_on')  # send command to Arduino
      print("Arduino LED turned on.")
   elif command == "k":  # turn off Arduino LED
      usb.write(b'led_off')  # send command to Arduino
      print("Arduino LED turned off.")
   elif command == "x":  # exit program
      print("Exiting program.")
      exit()
   else:  # unknown command
      print("Unknown command '" + command + "'.")
      print_commands()