# O Arduino espera por um comando do Raspberry Pi (por USB) para adquirir um valor
# analógico de uma das suas entradas analógicas
# Se o comando não for o correcto envia uma mensagem de erro ao Raspberry Pi
# Se o comando for o correcto envia o valor adquirido de volta ao Raspberry Pi por USB

USB_PORT = "/dev/ttyACM0"

void setup() // runs once when the sketch starts
{
  // make the LED pin (pin 13) an output pin
  pinMode(ledPin, OUTPUT);

  // initialize serial communication
  Serial.begin(9600);
  while(!Serial){}
}

void loop() // runs repeatedly after setup() finishes
{
  sensorValue = analogRead(sensorPin);  // read pin A0   
  Serial.println(sensorValue);         // send data to serial

  if (sensorValue < 500) {            // less than 500?
    digitalWrite(ledPin, LOW); }     // Turn the LED off

  else {                               // greater than 500?
    digitalWrite(ledPin, HIGH); }     // Keep the LED on

  delay(100);             // Pause 100 milliseconds
}