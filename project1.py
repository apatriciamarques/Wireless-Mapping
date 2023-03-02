#Trabalho 1 - Aquisição de dados e comunicação
#Corre um programa Python (3) em janela Qt (PyQt5, com comandos por botão
#start/stop/comando), com uma janela pyqtgraph, onde coloca os valores recebidos do Arduino
#num gráfico xy (plot)
#- Envia a intervalos definidos um comando ao Arduíno para que este adquira um valor
#analógico e o envie
#- Imprime esse valor, e actualiza o plot


#from numpy import ndarray
#from pandas import DataFrame, read_csv, unique

#import PyQt5
import pyqtgraph
import os
import serial
import numpy
import sys
from PyQt5.QtCore import QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtGui import QIcon

def window():
   app = QApplication(sys.argv)
   widget = QWidget()
   
   button1 = QPushButton(widget)
   button1.setText("Start")
   button1.move(64,32)
   button1.clicked.connect(button1_clicked)

   button2 = QPushButton(widget)
   button2.setText("Stop")
   button2.move(64,64)
   button2.clicked.connect(button2_clicked)

   button3 = QPushButton(widget)
   button3.setText("Comando")
   button3.move(64,96)
   button3.clicked.connect(button3_clicked)

   widget.setGeometry(50,50,320,200)
   widget.setWindowTitle("IAD")
   widget.show()
   sys.exit(app.exec_())


def button1_clicked():
   print("Button 1 clicked")

def button2_clicked():
   print("Button 2 clicked") 

def button3_clicked():
   print("Button 3 clicked")   
   
if __name__ == '__main__':
   window()
