//---------------------------------//
//    IAD - Projeto Introdutório   //
// Bruno Semião, Eduarda Assunção, //
// Sofia Simenta, Patrícia Marques //
//---------------------------------//

#include "SoftwareSerial.h"
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

SoftwareSerial bluetooth(7, 8);//Create a serial connection with TX and RX on these pins
Adafruit_MPU6050 mpu;

int PinSensorR = 10;
int PinSensorF = 9;
String command;
int A_num = -1;
float distance;
unsigned long duration;

int PinPWML = 3;
int PinInvL = 2;
int PinPWMR = 5;
int PinInvR = 4;

int PinSenR = 10;
int PinSenF = 9;

int  speedL = -1;
int  speedR = -1;
bool invertL = LOW;
bool invertR = LOW;

String  state;

sensors_event_t a, g, temp;

void setup() {
   
   Serial.begin(9600);  //Start serial communication at baudrate 9600
   bluetooth.begin(9600); //Initialize communications with the bluetooth module
   
   pinMode(PinPWML, OUTPUT);
   pinMode(PinInvL, OUTPUT);
   pinMode(PinPWMR, OUTPUT);
   pinMode(PinInvR, OUTPUT);
   //pinMode(sigPin, OUTPUT); // Sets the trigPin as an Output
   //pinMode(sigPin, INPUT); // Sets the echoPin as an Input
   while(!Serial){};
   while(!bluetooth){};
   while (!mpu.begin()) {
     //Serial.println("Failed to find MPU6050 chip");
     delay(10);
   }
   //Serial.println("MPU6050 Found!");
   mpu.setAccelerometerRange(MPU6050_RANGE_2_G);
   mpu.setGyroRange(MPU6050_RANGE_250_DEG);
   mpu.setFilterBandwidth(MPU6050_BAND_44_HZ);
}

void loop(){  
  if (bluetooth.available()>0){  
    command = bluetooth.readStringUntil('\n');  
    if (command.startsWith("+")){return;}
    Serial.println(command);

    //Control speed
    speedL = command.substring(0,3).toInt()-100;
    speedR = command.substring(3,6).toInt()-100;
    invertL = command.substring(6,7).toInt();
    invertR = command.substring(7,8).toInt();

    analogWrite(PinPWML, speedL);
    digitalWrite(PinInvL, invertL);
    analogWrite(PinPWMR, speedR);
    digitalWrite(PinInvR, invertR);
  }
  //Sensor data
    pinMode(PinSensorF, OUTPUT);
    digitalWrite(PinSensorF, LOW);
    delayMicroseconds(2);
    digitalWrite(PinSensorF, HIGH);
    delayMicroseconds(10);
    digitalWrite(PinSensorF, LOW);
    pinMode(PinSensorF, INPUT);
    state = String(pulseIn(PinSensorF, HIGH)) + "!";

    pinMode(PinSensorR, OUTPUT);
    digitalWrite(PinSensorR, LOW);
    delayMicroseconds(2);
    digitalWrite(PinSensorR, HIGH);
    delayMicroseconds(10);
    digitalWrite(PinSensorR, LOW);
    pinMode(PinSensorR, INPUT);
    state += String(pulseIn(PinSensorR, HIGH)) + "!";

    mpu.getEvent(&a, &g, &temp);
    
    state += String(a.acceleration.x) + "!";
    state += String(a.acceleration.y) + "!";
    state += String(a.acceleration.z) + "!";
    state += String(g.gyro.x) + "!";
    state += String(g.gyro.y) + "!";
    state += String(g.gyro.z) + "!";
    
    bluetooth.println(state);
}
