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
import pyqtgraph
import os
import serial
import numpy

#project
from PyQt5.QtWidgets import QApplication, QWidget
import sys

app = QApplication(sys.argv)

# Create a Qt widget, which will be our window.
window = QWidget()
window.show()  
# Start the event loop.
app.exec()
