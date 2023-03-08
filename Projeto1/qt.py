import sys
import time
import serial
from time import sleep

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
 
TIME_STEP = 0.01
isRun = True

class Worker(QObject):
    finished = pyqtSignal()
    signalData = pyqtSignal(float)
    USB_PORT = "/dev/ttyACM0"

    def setupUSB(self):
        try:
            self.usb = serial.Serial(self.USB_PORT, 9600, timeout=1)
            print("Connected successfully\n\n")
        except:
            print("OOPSIE - Could not open USB serial port. O ACM já mudou de número...")
            print("Exiting program.")
            exit()

        try:
            #Clear input
            #time.sleep(4) #HE BE SLOW // DO NOT MEXATE
            self.usb.reset_input_buffer() 
        except:
            print("OOPSIE - Couldn't clear Input Buffer!")

    def GetData(self):
        global isRun
        while isRun:
            self.usb.write("gda\n".encode('utf-8'))
            while self.usb.in_waiting <= 0 and isRun: 
                time.sleep(0.01)
            self.line = self.usb.readline().decode('utf-8')
            self.signalData.emit(float(self.line))
            sleep(TIME_STEP)
        self.finished.emit()

        

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    def setup(self):
        #Create and setup worker to get data
        self.worker = Worker()
        self.worker.setupUSB()
        #Create a QThread object
        self.thread = QThread()
        #Move worker to the thread
        self.worker.moveToThread(self.thread)
        #Connect signals and slots
        self.thread.started.connect(self.worker.GetData)
        self.worker.finished.connect(self.thread.quit)
        self.worker.signalData.connect(self.UpdateGraph)

        #Create Data Handler
        self.time = []
        self.volt = []
        self.stop_time = 0

        #Create Window
        self.setWindowTitle("IAD - Beautiful Data")
        self.resize(1000, 500)
       
        #Create Main Widget for Layout
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        #Create and connect widgets 
        #Plot
        self.graphWidget = pg.PlotWidget()
        self.plotWidget = self.graphWidget.plot()

        #Start Button
        self.BtStart = QPushButton("Start", self)
        self.BtStart.clicked.connect(self.FStart)

        #Stop Button
        self.BtStop = QPushButton("Stop", self)
        self.BtStop.clicked.connect(self.FStop)
        self.BtStop.setEnabled(False)

        #____________ADD Vibes Button______________

        # Set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.graphWidget)
        hbox = QHBoxLayout()
        hbox.addWidget(self.BtStart)
        hbox.addWidget(self.BtStop)
        #layout.addStretch()
        layout.addLayout(hbox)
        self.centralWidget.setLayout(layout)

    def FStop(self):
        global isRun
        isRun = False
        self.stop_time += time.time()-self.start_time

        self.BtStop.setEnabled(False)
        self.BtStart.setEnabled(True)  

    def UpdateGraph(self, v):
        if isRun: #To prevent final data point when Stop Button is pressed      
            if(len(self.volt)>100): #Make sliding graph
                del self.volt[0]
                del self.time[0]
            self.volt.append(v)
            self.time.append(time.time()-self.start_time+self.stop_time)
            self.graphWidget.removeItem(self.plotWidget)
            self.plotWidget = self.graphWidget.plot(self.time, self.volt)
        print(self.time[-1]-self.time[-2])

    def FStart(self):
        global isRun
        isRun = True
        self.start_time = time.time()
        #Disable Button
        self.BtStart.setEnabled(False)
        self.BtStop.setEnabled(True)
        # Step 6: Start the thread
        self.thread.start()

    def OnClose(self):
        #Clear threads and workers
        self.worker.deleteLater()
        self.thread.deleteLater()

        

app = QApplication(sys.argv)
win = Window()
win.show()
execApp = app.exec()
win.OnClose()
sys.exit(execApp)


'''
    def run(self):
        """Long-running task."""
        for i in range(5):
            sleep(1)
            self.progress.emit(i + 1)
        self.finished.emit()
'''
'''
        self.thread.finished.connect(
            lambda: self.BtStart.setEnabled(True)
        )
'''
