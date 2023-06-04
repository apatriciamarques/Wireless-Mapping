import sys
import time
import serial
import math
from time import sleep
import numpy as np
from PIL import Image as im
from PIL import ImageOps as ops

import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtGui import QDoubleValidator, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLineEdit,
)

# ************** Uncomment this to check available ports **************
# import serial.tools.list_ports
# ports = serial.tools.list_ports.comports()
# for port, desc, hwid in sorted(ports):
#         print(f"{port}: {desc} [{hwid}]\n")

#Worker in secondary thread
class Worker(QObject):

    #Signals
    finished   = pyqtSignal()
    stop_error = pyqtSignal()
    signalData = pyqtSignal(float)
    update_img = pyqtSignal()

    #Parameters
    mode        = 0                  #0-Map with acc; 1-Map without acc; 2-Map rotating; 3-WASD Control
    BT_PORT     = "COM8"
    time_step   = 0.05
    calib_time  = 5
    
    #Rescaling constants
    rescaleK   = 5
    rotationK  = 0.999
    positionK  = 1.8

    offsetW    = -0.01
    offset_acc = 0
    sd_acc     = 0

    #Default movement (stopped)
    speedL  = 100       #Speed left wheel
    speedR  = 100       #Speed right wheel
    invL    = 0         #Invert left wheel
    invR    = 0         #Invert right wheel
    sensorF = 30000
    sensorR = 30000

    #Data storage
    acceleration = 0
    velocityW    = 0
    velocity     = 0
    phi          = math.pi
    PhiI         = 0. 
    v0           = 390.
    time         = []
    currentTime  = 0.
    oldTime      = 0.
    timeDelta    = 0.
    line         = ""
    key          = " "

    #Flags
    isRun           = True
    input           = 0
    isSense         = 1
    isMoving        = 0
    foundObject     = 0
    temp            = 1

    #Image defaults  
    IMAGE_SIZE  = 1000
    position    = [int(IMAGE_SIZE*0.75), int(IMAGE_SIZE*0.75)]
    img = im.new(mode="RGB", size=(IMAGE_SIZE, IMAGE_SIZE), color=(255,255,255))

    #Setup Bluetooth connection at beggining of execution
    def setupBluetooth(self):
        #Connect
        try:
            self.bluetooth = serial.Serial(self.BT_PORT, 9600, timeout=1)
            self.bluetooth.write_timeout = 0.1
            print(f"Connected successfully to {self.BT_PORT}\n\n")
        except:
            print(f"OOPSIE - Could not connect to bluetooth port {self.BT_PORT}!\nExiting program.")
            exit()
        
        #Clear input buffer
        try:
            self.bluetooth.flushInput()
            self.bluetooth.flushOutput()
        except:
            print("OOPSIE - Couldn't clear Input Buffer!")

    #Exchange info with Arduino
    def Read_BT(self):
        while self.bluetooth.in_waiting <= 0 and self.isRun:      #Wait until data is available
            time.sleep(0.005)
        try:
            self.line = self.bluetooth.readline().decode('utf-8').split("!")
        except:
            print("Failed to Read")

    #Draw position with box of 3x3 pixels, if possible            
    def draw_position(self, x, y, r, g, b):
        x = int(x/self.rescaleK)
        y = int(y/self.rescaleK)
        if x - 1 > 0 and x + 2 < self.IMAGE_SIZE and y - 1> 0 and y + 2 < self.IMAGE_SIZE:
            for i in range(y - 1, y + 2):
                for j in range(x - 1, x + 2):
                    self.img.putpixel((i,j), (r,g,b))

    #Choosing graph variable
    def graphDictionary(self):
        match self.input:
            case 0: return self.acceleration
            case 1: return self.velocity
            case 2: return self.velocityW
            case 3: return self.phi
            case 4: return self.sensorF
            case 5: return self.sensorR

    #Control speed of the wheels
    def MovementHandler(self, val, speed):
        match val:
            case -1:                # Move Backwards
                self.speedL   = 100
                self.speedR   = 100
                self.invL     = 1
                self.invR     = 1
                self.isMoving = 0
            case 0:                 # Stoped
                self.speedL   = 100
                self.speedR   = 100
                self.invL     = 0
                self.invR     = 0
                self.isMoving = 0
            case 1:                 # Forward
                correction = int(400*(self.phi - 1.57075 * round(self.phi/1.57075, 0)))   #Get diference to nearest multiple of pi/2
                if correction > 100:
                    correction = 100
                elif correction < -100:
                    correction = -100

                self.speedL   = 255 + correction
                self.speedR   = 255 - correction
                self.invL     = 0
                self.invR     = 0
                self.isMoving = 1
            case 11:                # Fast Forward
                self.speedL   = 355
                self.speedR   = 355
                self.invL     = 0
                self.invR     = 0
                self.isMoving = 1
            case 2:                 # Left 90º turn
                self.speedL   = 355 - speed
                self.speedR   = 100 + speed
                self.invL     = 1
                self.invR     = 0
                self.isMoving = 0
            case 22:                # Fast Left Turn
                self.speedL   = 155
                self.speedR   = 300
                self.invL     = 1
                self.invR     = 0
                self.isMoving = 0
            case 3:                 # Right 90º turn
                self.speedL   = 100 + speed
                self.speedR   = 355 - speed
                self.invL     = 0
                self.invR     = 1
                self.isMoving = 0
            case 33:                # Fast Right Turn
                self.speedL   = 300
                self.speedR   = 155
                self.invL     = 0
                self.invR     = 1
                self.isMoving = 0
        
    #Constant speed calibration
    def calibrate_linear(self):
        calib_velocity = []
        timeI_calib = self.currentTime
        print("A calibrar. Espero não bater! :)")

        while self.isCalib:
            if self.sensorF > 400:          #Move while far from obstacle
                self.MovementHandler(1,0)
            else:                           #When close to obstacle stop moving and end calibration
                self.isCalib = 0
                self.MovementHandler(0,0)

            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))
            self.Read_BT()
            
            #Get iteration time 
            try:
                self.timeDelta = self.time[-1]-self.time[-2]
            except:
                self.timeDelta = self.currentTime

            #Calculate angle
            self.velocityW = float(self.line[7]) - self.offsetW 
            self.phi += self.velocityW * self.timeDelta * self.rotationK

            #When moving at constant speed
            if self.isCalib and self.currentTime - timeI_calib > 0.6:
                calib_velocity.append(float(self.sensorF-int((int(self.line[0]) + 580)*0.1754 ))/self.timeDelta)         

            #Get distance in mm considering the center of the wheels
            self.sensorF = int((int(self.line[0]) + 580)*0.1754 ) 
            
            try:
                self.signalData.emit(self.graphDictionary())
            except:
                print("Failed calibration.")
                self.stop_error.emit()            

        #Moving velocity
        self.v0 = np.mean(calib_velocity)
        print(f"Calibrated! Velocity: {self.v0} mm/s")

    #Accelerometer calibration
    def calibrate_acc(self):
        calib_acceleration = []
        print("A calibrar. Não mexer!")

        while self.currentTime < self.calib_time:
            self.MovementHandler(0, 0)
            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))
            self.Read_BT()

            try:
                #Get angular velocity
                self.velocityW = float(self.line[7]) - self.offsetW

                #Get angle
                self.phi += self.velocityW * self.timeDelta * self.rotationK

                #Get accelerations
                calib_acceleration.append(float(self.line[2])*1000)
                
                self.signalData.emit(self.graphDictionary())
            except:
                print("Failed calibration.")
                self.stop_error.emit()            

        self.offset_acc = round(np.mean(calib_acceleration), 4)
        self.sd_acc = round(np.std(calib_acceleration), 4)
                           
        print(f"Calibrated! Angular velocity offset: {self.offsetW}\nAcceleration offset: {self.offset_acc}\n Acceleration Standard Deviation: {self.sd_acc}\n")

    #Main control loop
    def MasterControl(self):

        #-------------------------------- Map with acc ------------------------------
        
        if self.mode == 0:              
            #Calibrate and set initital position to right lower corner
            self.calibrate_acc()
            self.position[0] = int(self.IMAGE_SIZE*0.75*self.rescaleK)
            self.position[1] = int(self.IMAGE_SIZE*0.75*self.rescaleK)

            #Write first time to get response
            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))   #Request data
            
            while self.isRun:
                self.Read_BT()

                try:
                    #Get iteration time
                    try:
                        self.timeDelta = self.time[-1]-self.time[-2]
                    except:
                        self.timeDelta = self.currentTime

                    #Get movement parameters
                    self.velocityW = float(self.line[7]) - self.offsetW 
                    self.phi += self.velocityW * self.timeDelta * self.rotationK

                    self.acceleration = -self.offset_acc + (float(self.line[2])*1000)
                    if(abs(self.acceleration) < 2*self.sd_acc): #Remove small random variations
                        self.acceleration = 0
                    
                    #When the movement is purely rotational or is stopped, set linear velocity to 0
                    if(self.isMoving):
                        self.velocity += float(self.acceleration) * self.timeDelta
                    else:
                        self.velocity = 0

                    #Get distance in mm considering the center of the wheels
                    self.sensorF = int((int(self.line[0]) + 580)*0.1754 )
                    self.sensorR = int((int(self.line[1]) +  333)*0.1754 ) 

                    self.position[0] += int(self.positionK*self.velocity * self.timeDelta * math.cos(self.phi) )
                    self.position[1] += int(self.positionK*self.velocity * self.timeDelta * math.sin(self.phi) )
                    
                    self.signalData.emit(self.graphDictionary())
                except:
                    print("Failed to deal with Bluetooth data... Será que algum cabo se soltou?")
                    self.stop_error.emit()

                #Plot Car Position
                self.draw_position(self.position[0],self.position[1],100,200,0)

                if self.isSense == 1:

                    #--------------------Plot Objects----------------------
                    
                    #Found object on the right
                    if self.sensorR < 400:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorR * math.cos(self.phi - math.pi * 0.5) - 85. * math.cos(self.phi))
                        position_y_obj = math.floor( self.position[1] + self.sensorR * math.sin(self.phi - math.pi * 0.5) - 85. * math.sin(self.phi))
                
                        self.draw_position(position_x_obj,position_y_obj,0,0,255)

                    #Found object on the front
                    if self.sensorF < 550:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorF * math.cos(self.phi) )
                        position_y_obj = math.floor( self.position[1] + self.sensorF * math.sin(self.phi) )
                        
                        self.draw_position(position_x_obj,position_y_obj,255,0,0)
                    
                    #-------------------Movement Decision------------------
                    
                    #Default decision maker
                    if self.temp == 1:
                        if self.sensorF < 400:                          #Rotate counterclockwise to avoid obstacle
                            self.PhiI = self.phi
                            self.temp = 2   
                        elif self.sensorR > 400 and self.foundObject:   #Rotate clockwise to find object
                            self.PhiI = self.phi
                            self.temp = 3
                        else:                                           #Move forward
                            self.MovementHandler(1,0)
                    
                    #90 degree counterclockwise movement 
                    if self.temp == 2:
                        if abs(self.PhiI - self.phi) < 0.8:         #Rotate unti 90º
                            self.MovementHandler(2,180)
                        else:                                       #Calibrate after rotation
                            self.MovementHandler(0,0)
                            self.calib_time = self.currentTime + 5
                            self.calibrate_acc()
                            self.temp = 1

                    #90 degree clockwise movement
                    if self.temp == 3:
                        if abs(self.PhiI - self.phi) < 0.8:         #Rotate unti 90º
                            self.MovementHandler(3,180)
                        else:                                       #Calibrate after rotation
                            self.MovementHandler(0,0)
                            self.foundObject = 0
                            self.calib_time = self.currentTime + 5
                            self.calibrate_acc()
                            self.temp = 1

                self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8')) 
                self.update_img.emit()
                sleep(self.time_step)                               

        #------------------------------ Map without acc -----------------------------

        elif self.mode == 1:
            #Calibrate and set initital position to right lower corner
            self.position[0] = int(self.IMAGE_SIZE*0.25*self.rescaleK)
            self.position[1] = int(self.IMAGE_SIZE*0.75*self.rescaleK)
            self.isCalib = 1
            self.calibrate_linear()
            self.inicio_movimento = self.currentTime

            #Write first time to get response
            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))   #Request data
            
            while self.isRun:
                self.Read_BT()
                
                try:
                    #Get iteration time
                    try:
                        self.timeDelta = self.time[-1]-self.time[-2]
                    except:
                        self.timeDelta = self.currentTime

                    #Get movement parameters
                    self.velocityW = float(self.line[7]) - self.offsetW
                    self.phi += self.velocityW * self.timeDelta * self.rotationK

                    #When the movement is purely rotational or is stopped, set linear velocity to 0
                    if(self.isMoving):
                        if self.currentTime - self.inicio_movimento < 0.6:
                            self.velocity = (self.v0/0.6)*(self.currentTime - self.inicio_movimento)
                        elif self.currentTime - self.inicio_rotacao < 0.25:
                            self.velocity = self.v0 - (self.v0/0.25)*(self.currentTime - self.inicio_rotacao)
                        else:
                            self.velocity = self.v0
                        if self.velocity < 0:
                            self.velocity = 0
                            self.isMoving = 0
                    else:
                        self.velocity = 0

                    #Get distance in mm considering the center of the wheels
                    self.sensorF = int((int(self.line[0]) + 580)*0.1754 )
                    self.sensorR = int((int(self.line[1]) +  333)*0.1754 )

                    self.position[0] += int(self.positionK * self.velocity * self.timeDelta * math.cos(self.phi) )
                    self.position[1] += int(self.positionK * self.velocity * self.timeDelta * math.sin(self.phi) )
                    
                    self.signalData.emit(self.graphDictionary())
                except:
                    print("Failed to deal with Bluetooth data... Será que algum cabo se soltou?")
                    self.stop_error.emit()

                #Plot Car Position
                self.draw_position(self.position[0],self.position[1],100,200,0)

                if self.isSense == 1:

                    #--------------------Plot Objects----------------------

                    #Found object on the right
                    if self.sensorR < 400:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorR * math.cos(self.phi - math.pi * 0.5) - 85. * math.cos(self.phi))
                        position_y_obj = math.floor( self.position[1] + self.sensorR * math.sin(self.phi - math.pi * 0.5) - 85. * math.sin(self.phi))
                
                        self.draw_position(position_x_obj,position_y_obj,0,0,255)

                    #Found object on the front
                    if self.sensorF < 550:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorF * math.cos(self.phi) )
                        position_y_obj = math.floor( self.position[1] + self.sensorF * math.sin(self.phi) )
                        
                        self.draw_position(position_x_obj,position_y_obj,255,0,0)

                    #-------------------Movement Decision------------------
                    
                    #Default decision maker
                    if self.temp == 1:
                        if self.sensorF < 400:                          #Rotate counterclockwise to avoid obstacle
                            self.foundObject = 1
                            self.PhiI = self.phi
                            self.temp = 2
                            self.inicio_rotacao = self.currentTime
                        elif self.sensorR > 400 and self.foundObject:   #Rotate clockwise to find object
                            self.PhiI = self.phi
                            self.temp = 3
                            self.inicio_rotacao = self.currentTime
                        else:                                           #Move forward
                            self.MovementHandler(1,0)
                    
                    #90 degree counterclockwise movement 
                    if self.temp == 2:
                        if abs(self.PhiI - self.phi) < 0.8:         #Rotate unti 90º
                            self.MovementHandler(2,180)
                        else:
                            self.MovementHandler(0,0)
                            self.temp = 1
                            self.inicio_movimento = self.currentTime

                    #90 degree clockwise movement
                    if self.temp == 3:
                        if abs(self.PhiI - self.phi) < 0.8:         #Rotate unti 90º
                            self.MovementHandler(3,180)
                        else:
                            self.temp = 1
                            self.foundObject = 0
                            self.MovementHandler(0,0)
                            self.inicio_movimento = self.currentTime    
                    
                self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8')) 
                self.update_img.emit()
                sleep(self.time_step)                               

        #--------------------------------- Map rotating -------------------------------

        elif self.mode == 2:
            
            #Purely rotational movement
            self.isMoving = 0

            #Write first time to get response
            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))   #Request data
            
            while self.isRun:      
                self.Read_BT()
                
                try:
                    #Get iteration time
                    try:
                        self.timeDelta = self.time[-1]-self.time[-2]
                    except:
                        self.timeDelta = self.currentTime

                    #Get movement parameters and sensor data
                    self.velocityW = float(self.line[7]) - self.offsetW 
                    self.phi += self.velocityW * self.timeDelta * self.rotationK

                    self.sensorF = int((int(self.line[0]) + 580)*0.1754 )
                    self.sensorR = int((int(self.line[1]) +  333)*0.1754 )

                    self.position[0] = int(self.rescaleK*self.IMAGE_SIZE/2.)
                    self.position[1] = int(self.rescaleK*self.IMAGE_SIZE/2.)
                    
                    self.signalData.emit(self.graphDictionary())
                except:
                    print("Failed to deal with Bluetooth data... Será que algum cabo se soltou?")
                    self.stop_error.emit()

                #Plot Car Position
                self.draw_position(self.position[0],self.position[1],100,200,0)

                if self.isSense == 1:

                    #--------------------Plot Objects----------------------

                    #Found object on the right
                    if self.sensorR < 400:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorR * math.cos(self.phi - math.pi * 0.5) - 85. * math.cos(self.phi))
                        position_y_obj = math.floor( self.position[1] + self.sensorR * math.sin(self.phi - math.pi * 0.5) - 85. * math.sin(self.phi))
                
                        self.draw_position(position_x_obj,position_y_obj,0,0,255)

                    #Found object on the front
                    if self.sensorF < 550:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorF * math.cos(self.phi) )
                        position_y_obj = math.floor( self.position[1] + self.sensorF * math.sin(self.phi) )
                        
                        self.draw_position(position_x_obj,position_y_obj,255,0,0)
                    
                    #-------------------Movement Decision------------------
                    #Always rotate
                    if self.isRun:
                        self.MovementHandler(2, 130)

                self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8')) 
                self.update_img.emit()
                sleep(self.time_step)                               

        #---------------------------------- WASD Control --------------------------------
        
        elif self.mode == 3:
            #Set initial position
            self.position[0] = int(self.rescaleK*self.IMAGE_SIZE/2.)
            self.position[1] = int(self.rescaleK*self.IMAGE_SIZE/2.)
            
            #Write first time to get response
            self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))   #Request data
            
            while self.isRun:
                self.Read_BT()

                try:
                    #Get iteration time
                    try:
                        self.timeDelta = self.time[-1]-self.time[-2]
                    except:
                        self.timeDelta = self.currentTime

                    #Get movement parameters
                    self.velocityW = float(self.line[7]) - self.offsetW 
                    self.phi += self.velocityW * self.timeDelta * self.rotationK

                    self.acceleration = -self.offset_acc + (float(self.line[2])*1000) 
                    if(abs(self.acceleration) < 2*self.sd_acc): #Remove small random variations
                        self.acceleration = 0
                    
                    #When the movement is purely rotational or is stopped, set linear velocity to 0
                    if(self.isMoving):
                        self.velocity += float(self.acceleration) * self.timeDelta
                    else:
                        self.velocity = 0

                    #Get distance in mm considering the center of the wheels
                    self.sensorF = int((int(self.line[0]) + 580)*0.1754 ) 
                    self.sensorR = int((int(self.line[1]) +  333)*0.1754 ) 

                    self.position[0] += int(self.positionK*self.velocity * self.timeDelta * math.cos(self.phi) )
                    self.position[1] += int(self.positionK*self.velocity * self.timeDelta * math.sin(self.phi) )
                    
                    self.signalData.emit(self.graphDictionary())
                except:
                    print("Failed to deal with Bluetooth data... Será que algum cabo se soltou?")
                    self.stop_error.emit()

                #Plot Car Position
                self.draw_position(self.position[0],self.position[1],100,200,0)

                if self.isSense == 1:

                    #--------------------Plot Objects----------------------

                    #Found object on the right
                    if self.sensorR < 400:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorR * math.cos(self.phi - math.pi * 0.5) - 85. * math.cos(self.phi))
                        position_y_obj = math.floor( self.position[1] + self.sensorR * math.sin(self.phi - math.pi * 0.5) - 85. * math.sin(self.phi))
                
                        self.draw_position(position_x_obj,position_y_obj,0,0,255)

                    #Found object on the front
                    if self.sensorF < 550:
                        # Position of obstacle based on angle and distance
                        position_x_obj = math.floor( self.position[0] + self.sensorF * math.cos(self.phi) )
                        position_y_obj = math.floor( self.position[1] + self.sensorF * math.sin(self.phi) )
                        
                        self.draw_position(position_x_obj,position_y_obj,255,0,0)

                #---------------------Movement Requests---------------------

                match self.key:
                    case 'w':
                        if self.sensorF > 350:
                            self.MovementHandler(11,0)
                        else:
                            self.MovementHandler(0,0)
                    case 's':
                        self.MovementHandler(-1,0)
                    case 'a':
                        if self.sensorR > 150:
                            self.MovementHandler(22,0)
                        else:
                            self.MovementHandler(0,0)
                    case 'd':
                        self.MovementHandler(33,0)
                    case 'q':
                        self.MovementHandler(0,0)

                self.bluetooth.write(f"{self.speedL}{self.speedR}{self.invL}{self.invR}\n".encode('utf-8'))
                self.update_img.emit()
                sleep(self.time_step)      
                
        self.finished.emit()                                    #Emit "finished" to release thread

        

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup()

    #Setup program
    def setup(self):
        #Data Handlers and default values
        self.graph = []
        self.stop_time = 0.
        self.timeRange = 5.
        self.slideGr = False
        #Create and setup worker thread
        self.worker = Worker()
        self.worker.setupBluetooth()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        #Connect signals to worker thread
        self.thread.started.connect(self.worker.MasterControl)
        self.worker.finished.connect(self.thread.quit)
        self.worker.signalData.connect(self.UpdateGraph)
        self.worker.stop_error.connect(self.FStop)
        self.worker.update_img.connect(self.UpdateImage)

        #----------Setup GUI----------
        self.setWindowTitle("IAD 2.0 - Carrito Lindito")
        self.resize(1000, 500)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        #Plot
        self.graphWidget = pg.PlotWidget()
        self.plotWidget = self.graphWidget.plot()
        self.graphWidget.setBackground('k')
        self.graphWidget.setLabel('left', "<span style=\"color:white;font-size:17px\">Voltage (V)</span>")
        self.graphWidget.setLabel('bottom', "<span style=\"color:white;font-size:17px\">Time (s)</span>")
        self.graphWidget.showGrid(x=True, y=True)
        self.graphWidget.setXRange(0, self.timeRange)

        #Label Mode
        self.lbMode = QLabel("\tMode:", self)

        #Modo Acc Button
        self.BtAcc = QPushButton("Map w/ accelerometer", self)
        self.BtAcc.setCheckable(True)
        self.BtAcc.setStyleSheet("background-color : lightgreen")
        self.BtAcc.clicked.connect(self.FAcc)

        #Modo V0 Button
        self.BtV0 = QPushButton("Map w/o accelerometer", self)
        self.BtV0.setCheckable(True)
        self.BtV0.setStyleSheet("background-color : lightblue")
        self.BtV0.clicked.connect(self.FV0)

        #Modo Rot Button
        self.BtRot = QPushButton("Map Rotation", self)
        self.BtRot.setCheckable(True)
        self.BtRot.setStyleSheet("background-color : rgb(250,200,200)")
        self.BtRot.clicked.connect(self.FRot)

        #Modo Tele Button
        self.BtTele = QPushButton("User Control", self)
        self.BtTele.setCheckable(True)
        self.BtTele.setStyleSheet("background-color : lightyellow")
        self.BtTele.clicked.connect(self.FTele)

        #Input Selector Combo Box and Label
        self.lbInput = QLabel("\tGraph:", self)
        self.cbInput = QComboBox(self)
        self.cbInput.addItem('Aceleration')
        self.cbInput.addItem('Linear Velocity')
        self.cbInput.addItem('Angular Velocity')
        self.cbInput.addItem('Trajectory Angle')
        self.cbInput.addItem('Front Sensor')
        self.cbInput.addItem('Right Sensor')
        self.cbInput.currentIndexChanged.connect(self.FInputChange)

        #Time Range Widgets
        self.leRangeT = QLineEdit(f'{self.timeRange}', self)
        self.leRangeT.setValidator(QDoubleValidator(0.1, 300.0, 1))
        self.leRangeT.textChanged.connect(self.FlRangeT)
        self.lbRangeT = QLabel("\tTime Range:", self)

        #Time Step Widgets
        self.leTimeStep = QLineEdit(f'{self.worker.time_step}', self)
        self.leTimeStep.setValidator(QDoubleValidator(0.05, 300.0, 2))
        self.leTimeStep.textChanged.connect(self.FtimeStep)
        self.lbTimeStep = QLabel("\tTime Step:", self)

        #Movement Box
        self.leMove = QLineEdit(self)
        self.leMove.textChanged.connect(self.FMove)
        self.lbMove = QLabel("\tWASD:", self)
        self.leMove.setReadOnly(True)

        #Image 
        self.lbImg = QLabel(self)
        self.lbImg.setPixmap(QPixmap('img/default.jpg'))

        #Set the layout
        layout = QVBoxLayout()
        topbox = QHBoxLayout()
        topbox.addWidget(self.graphWidget)
        topbox.addWidget(self.lbImg)
        hbox = QHBoxLayout()
        hbox.addWidget(self.lbInput)
        hbox.addWidget(self.cbInput)
        hbox.addWidget(self.lbMode)
        hbox.addWidget(self.BtAcc)
        hbox.addWidget(self.BtV0)
        hbox.addWidget(self.BtRot)
        hbox.addWidget(self.BtTele)
        hbox.addWidget(self.lbMove)
        hbox.addWidget(self.leMove)
        hbox.addWidget(self.lbRangeT)
        hbox.addWidget(self.leRangeT)
        hbox.addWidget(self.lbTimeStep)
        hbox.addWidget(self.leTimeStep)
        layout.addLayout(topbox)
        layout.addLayout(hbox)
        self.centralWidget.setLayout(layout)

    #Update image map
    def UpdateImage(self):
        try:
            self.worker.img.save("img/tempImg.jpg")
            self.lbImg.setPixmap(QPixmap('img/tempImg.jpg'))
        except:
            self.lbImg.setPixmap(QPixmap('img/default.jpg'))

    #Handle WASD Control
    def FMove(self, key):
        if key:                      #Don't send empty spaces when clearing
            self.worker.key = key
            self.leMove.clear()

    #Time Step Handler
    def FtimeStep(self, val):
        try:
            if float(val) < 0.05:
                self.worker.time_step = 0.05
            elif float(val) > self.timeRange:
                self.worker.time_step = self.timeRange
                self.leTimeStep.setText(f"{self.worker.time_step}")
            else:
                self.worker.time_step = float(val)
            self.BtAcc.setEnabled(True)
            self.BtV0.setEnabled(True)
            self.BtRot.setEnabled(True)
            self.BtTele.setEnabled(True)
        except:
            self.BtAcc.setEnabled(False)
            self.BtV0.setEnabled(False)
            self.BtRot.setEnabled(False)
            self.BtTele.setEnabled(False)

    #Time Range Handler
    def FlRangeT(self, val):
        try:
            if float(val) < 0.1:
                self.timeRange = 0.1
            elif float(val) > 300:
                self.timeRange = 300
                self.leRangeT.setText("300.0")
            else:
                self.timeRange = float(val)
            self.graphWidget.setXRange(0, self.timeRange)
            self.BtAcc.setEnabled(True)
            self.BtV0.setEnabled(True)
            self.BtRot.setEnabled(True)
            self.BtTele.setEnabled(True)
        except:
            self.BtAcc.setEnabled(False)
            self.BtV0.setEnabled(False)
            self.BtRot.setEnabled(False)
            self.BtTele.setEnabled(False)

    #Input Selection Handler
    def FInputChange(self, index):
        self.worker.input = index

    #BtAcc Handler
    def FAcc(self):
        if self.BtAcc.isChecked():
            self.FStart()
            self.worker.mode = 0
            self.BtAcc.setStyleSheet("background-color : green")
            self.leMove.setReadOnly(True)
            self.BtV0.setEnabled(False)
            self.BtRot.setEnabled(False)
            self.BtTele.setEnabled(False)
        else:
            self.FStop()
            self.BtAcc.setStyleSheet("background-color : lightgreen")

    #BtV0 Handler
    def FV0(self):
        if self.BtV0.isChecked():
            self.FStart()
            self.worker.mode = 1
            self.BtV0.setStyleSheet("background-color : blue")
            self.leMove.setReadOnly(True)
            self.BtAcc.setEnabled(False)
            self.BtRot.setEnabled(False)
            self.BtTele.setEnabled(False)
        else:
            self.FStop()
            self.BtV0.setStyleSheet("background-color : lightblue")

    #BtRot Handler
    def FRot(self):
        if self.BtRot.isChecked():
            self.FStart()
            self.worker.mode = 2
            self.BtRot.setStyleSheet("background-color : rgb(200,100,100)")
            self.leMove.setReadOnly(True)
            self.BtAcc.setEnabled(False)
            self.BtV0.setEnabled(False)
            self.BtTele.setEnabled(False)
        else:
            self.FStop()
            self.BtRot.setStyleSheet("background-color : rgb(250,200,200)")

    #BtTele Handler
    def FTele(self):
        if self.BtTele.isChecked():
            self.FStart()
            self.worker.mode = 3
            self.BtTele.setStyleSheet("background-color : yellow")
            self.leMove.setReadOnly(False)
            self.BtAcc.setEnabled(False)
            self.BtV0.setEnabled(False)
            self.BtRot.setEnabled(False)
        else:
            self.FStop()
            self.BtTele.setStyleSheet("background-color : lightyellow")
            self.leMove.setReadOnly(True)

    #Clear Button Handler
    def FStop(self):
        self.worker.key = " "
        self.worker.isSense = 0
        self.worker.MovementHandler(0,0)
        time.sleep(0.3)
        self.worker.isRun = False
        self.slideGr = False
        self.worker.currentTime = 0.0
        self.graphWidget.setXRange(0, self.timeRange)
        self.graph.clear()
        self.worker.time.clear()
        self.graphWidget.clear()
        self.leRangeT.setReadOnly(False)
        self.leTimeStep.setReadOnly(False)
        self.leMove.setReadOnly(True)

    #Start Button Handler
    def FStart(self):
        self.worker.isSense = 1
        self.worker.isRun = True
        self.start_time = time.time()

        #Run checks
        if float(self.leRangeT.text()) < 0.1:
            self.leRangeT.setText("0.1")
        if float(self.leTimeStep.text()) < 0.05:
            self.leTimeStep.setText("0.05")
        if float(self.leRangeT.text()) < float(self.leTimeStep.text()):
            self.worker.time_step = self.timeRange
            self.leTimeStep.setText(f"{self.timeRange}")

        self.leRangeT.setReadOnly(True)
        self.leTimeStep.setReadOnly(True)

        #Start the thread
        self.thread.start()

    #Receive data and update plot
    def UpdateGraph(self, y):
        if self.worker.isRun:                           #To prevent final data point when Stop Button is pressed      
            self.worker.currentTime = time.time()-self.start_time+self.stop_time
            if self.slideGr == False:
                if(self.worker.currentTime > self.timeRange):  #Handle sliding graph
                    self.slideGr = True
                    self.graphWidget.enableAutoRange(axis='x', enable=True)      
            else:
                del self.graph[0]
                del self.worker.time[0]

            self.graph.append(y)
            self.worker.time.append(self.worker.currentTime)           
            self.graphWidget.removeItem(self.plotWidget)
            self.plotWidget = self.graphWidget.plot(self.worker.time, self.graph, pen=pg.mkPen(color='#E85D3F')) 

    #On closing app
    def OnClose(self):
        self.worker.isSense = 0
        self.worker.MovementHandler(0,0)
        sleep(0.2)
        self.worker.isRun = False
        #Clear threads and workers
        self.thread.quit()
        self.worker.deleteLater()
        self.thread.deleteLater() 
        

app = QApplication(sys.argv)
win = Window()
win.showMaximized()
execApp = app.exec()
win.OnClose()
sys.exit(execApp)



