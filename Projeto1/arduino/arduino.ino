void setup() {
   Serial.begin(9600);  // start serial communication at baudrate 9600
   while(!Serial){};
}

String command;
int analogVal;

void loop() {
   // Read and execute commands from serial port
   if (Serial.available() > 0) {  // check for incoming serial data
      command = Serial.readStringUntil('\n');  // read command from serial port
      if (command == "gda") {  // Get Data from Analog input
         analogVal = analogRead(0);
         Serial.println(String(analogVal));
      }
      else
      {
         Serial.println("OOPSIE - Comando não reconhecido!\n");
      }
   }
}
