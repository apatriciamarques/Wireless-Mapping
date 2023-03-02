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
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        button = QPushButton("Press Me!")

        button = QPushButton("Stop")

        button = QPushButton("Comando")

        self.setFixedSize(QSize(400, 300))

        # Set the central widget of the Window.
        self.setMenuWidget(button)

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
