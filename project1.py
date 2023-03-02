#Trabalho 1 - Aquisição de dados e comunicação
#Corre um programa Python (3) em janela Qt (PyQt5, com comandos por botão
#start/stop/comando), com uma janela pyqtgraph, onde coloca os valores recebidos do Arduino
#num gráfico xy (plot)
#- Envia a intervalos definidos um comando ao Arduíno para que este adquira um valor
#analógico e o envie
#- Imprime esse valor, e actualiza o plot


#from numpy import ndarray
#from pandas import DataFrame, read_csv, unique

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