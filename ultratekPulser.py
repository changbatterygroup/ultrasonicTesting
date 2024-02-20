# Code for connecting to an Ultratek CompactPulser, starting and stopping pulses, and disconnecting over a serial port
# Uses pyserial to connect and send commands. The pulser takes simple commands encoded as ascii ('string'.encode('ascii'))

import numpy as np
import serial

@dataclass
class PulserProperties:
    """Everything needed to configure Ultratek pulser."""
    damping: str = 'D0'
    mode: str = 'M0'
    pulse_voltage: str = 'V300'
    pulse_width: str = 'W220'
    pulse_repetition_rate: str = 'P500'
    mode: str = 'T0'  # internal
    # LPF: str = 'L2' #low pass filter of 48 MHz

# Opens pyserial connection to the pulser
# Input is a string name of the port (i.e. 'COM3')
# returns a serial class for the connection or -1 if an error occurred
#TODO: add confirmation, error handling, scanning for proper port
def openPulser(portName):
    #Note pyserial defaults match the ultratek connection parameters
    #For reference these are:
    #baudrate = 9600
    #bytesize = EIGHTBITS
    #parity = PARITY_NONE
    #stopbits = STOPBITS_ONE
    #xonxoff = False
    try:
        pulserSerial = serial.Serial(portName)

    except serial.SerialException as error:
        print(f"Error opening pulser: {error}")
        return -1

    else:
        return pulserSerial

# Function to send commands to the pulser. Useful for turning things on/off or adjusting parameters
# Inputs: serialConnection Serial object for the pulser and the string command to send
# Function adds a carriage return to the command, encodes it to ascii, then sends to the pulser
# TODO: add verification that message is received
def writeToPulser(serialConnection, command):
    commandString = command + '\r'

    try:
        serialConnection.write(commandString.encode('ascii'))

    except serial.SerialException as error:
        print(f"Error writing command to pulser: {error}")
        return -1

    else:
        return 0

# function to change the pulsing parameters
# takes a list of parameters and iterates through them with writeToPulser()
def pulserParameters(serialConnection, parameters):

    return 0

# Turns the pulser on at a pulse repetition frequency of 5000 Hz
# Returns None
# TODO: make frequency variable
def pulserOn(serialConnection):

    writeToPulser(serialConnection, 'P500')

# Turns off pulser by setting pulse repetition frequency to 0
# Returns None
def pulserOff(serialConnection):

    writeToPulser(serialConnection, 'P0')

# Closes serial connection to the pulser
# TODO: add confirmation, error handling
def closePulser(serialConnection):

    try:
        serialConnection.close()

    except serial.SerialException as error:
        print(f"Error closing pulser connection: {error}")
        return -1

    else:
        return 0