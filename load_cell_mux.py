from runExperiment import runExperiment
import numpy as np

def shuffled_arange():
    arr = np.arange(-50,50,5)
    np.random.shuffle(arr)
    return arr

# collectionMode = 'transmission'
# waves = 1000
# samples = 20000
# measureDelay = 4
# #
collectionMode = 'echo'
waves = 1000
samples = 15000
measureDelay = 3
#
autoRange = 0

###################################################################
#################  Operating Instructions  ########################
###################################################################
# 1) Decide which experiment you want to perform (move the transducers, take a single pulse,
# collect a 2D scan, or collect multiple 2D scans)
#
# 2) fill out the relevant parameters for each experiment
#
# 3) run this script. On PyCharm, simply press Shift + F10 or click the green play button at the top right


experimentParams = {
    # If you want to use the GUI, simply set 'gui' : True and the program will guide you through the rest of the setup
    'gui': False,
    # What do you want to do?
    #'move' = move the transducers
    #'single pulse' = perform a single test pulse
    #'repeat pulse' = repeat a pulse at a single location for a given time and frequency
    #'single scan' = perform a single 2D scan
    #'multi scan' = repeat a 2D scan with a set frequency
    #Once you have selected, fill out the values in the parameter list in the correct section
    #NOTE: ONLY CHANGE THE VALUES AFTER THE COLON ON EACH LINE
    # 'experiment': 'sweep',
    'experiment': 'single pulse',

    #####################################################################
    ################# 'move' parameters #################################
    ### Only applies when 'experiment' == 'move' ########################
    #####################################################################
    'axis': 'z',  # Axis to move scanner
    'distance':-20,  # Distance in mm to move scanner

    #################################################################################
    ###################### Ultrasonic Parameters #####################################
    #### Applies to 'single pulse', 'single scan', and 'multi scan' experiments #####
    #################################################################################

    'transducerFrequency': 2.25,
    # Central frequency of the ultrasonic transducer, in MHz. Current options are 2.25 or 50
    'collectionMode': collectionMode,  #transmission/echo/both
    'pulserType': 'standard',  # Type of pulser. 'standard' is the single wave CompactPulser. 'tone burst' uses the USBUT350 tone burst pulser
    'measureTime': 30,  # Changes to the measureTime will be printed in the console when the script is run
    'measureDelay': measureDelay,   # Approx delay after trigger to start measuring, in us
    'voltageRange': 2,  # Picoscope voltage range in V. Note this is the total range: 1 V = [-0.5 V, 0.5 V]
    # Allowed voltages = (0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20)
    # todo: separate autoRange and autoGain

    'autoRange': autoRange,
    # Set the oscilloscope to rerun measurements where the voltage range of the wave has significantly changed
    # This enables the tightest possible voltageRange to be used, increasing the accuracy of low intensity signals without cutting off high intensity ones
    # For transmission measurements, this changes the voltage range on the oscilloscope.
    # NOTE: this can add significant overhead (2-3x increase in collection time) for each waveform where the range changes
    'autoRangeEcho': autoRange,
    # Automatically calculate and adjust the offset and gain values. This may add significant measurement time
    'waves': waves,  # Number of waves to collect and average (waves*samples < 60,000,000)
    'samples': samples,  # Number of data points per wave (best resolution is 2ns-> (measureTime-measureDelay)/2*1000
    'halfCycles': 2,  # Tone burst pulser only. Number of half-cycles in a tone burst pulse. Minimum 1, maximum 32

    ##############################################################################################
    ######################## Advanced Options ####################################################
    ############# Parameters for multiplexed measurements ########################################
    ##############################################################################################

    #todo: add gain option here?
    'multiplexer': False,  # Will the multiplexer be used in the measurement
    # If set to False, all other parameters in this section are ignored
    # and the system is assumed to be wired without the multiplexer (trigger to Channel B, receiver or RF data to Channel A)

    'collectionDirection': 'forward',  # Specifies the channels used for the transmitting and receiving transducers
    # 'forward' pulses on Channel A and (for collectionMode = transmision or both) collects on Channel B
    # 'reverse' pulses on Channel B and collects on Channel A
    # 'both' repeats the measurement in both directions
    'voltageOffsetForward': 0.0,
    # Voltage offset applied to pulse-echo measurements to fix large baseline added by pulser output
    'voltageOffsetReverse': 0.0,
    #     Voltage offsets are directional since 1) echo baseline depends heavily on delay time and 2) delay time
    #     is a function of sample placement and could vary widely between the forward and reverse transducer
    'gainForward': 500,  # Gain setting on pulser, used to maximize the signal of pulse-echo measurements
    'gainReverse': 500,
    #  similar to voltageOffsets, these can be set to different values for the forward and reverse directions
    #todo: add pulse module and picoscope module, convert existing address params to just switch numbers
    # todo: will need to add code to pulse.init to build the addresses from inputs
    # advantage of this new method is safety - you cannot specify unsafe address combos
    'picoModule': 1,  # Row of the C port on the multiplexer connected to the Picoscope Channel A
    'pulseModule': 0,  # Row of the C port on the multiplexer connect to the pulser TX output

    'rfSwitch': 2,  # Column of the port on the picoModule row connected to the RF output of the pulser
    't0PulseSwitch': 3,  # Column of the port on pulseModule row connected to transducer 0
    't0ReceiveSwitch': 3,
    #   NOTE: all data channels (RF, transducer receive) should be on the same module as the picoscope
    't1PulseSwitch': 0,
    #         and all pulsing transducer channels should be on the same module as the TX (pulser output)
    't1ReceiveSwitch': 0,  #   If you are not using a particular channel, using None as the value will
    #   will enable error checking that the channels used are compatible with the chosen
    #   collectionMode and collectionDirection

    ################################################################################
    ########################### Saving Names ##########################################
    ##### Applies to 'single scan', 'multi scan', and 'repeat pulse' experiment ####
    ################################################################################

    'experimentFolder': 'C://Users//changlab//Desktop//UT Data//TMM_SS_characterization//',  # Name of folder to dump data "C:\Users\changlab\Desktop\UT Data"
    # Name of folder to dump data "C:\Users\changlab\Desktop\UT Data"
    'experimentName' : f'tall_rods_steel_steel_top',                  # File name for single scan and repeat pulse experiment. Will be appended with .json or .sqlite3
    # File name for single scan and repeat pulse experiment. Will be appended with .json or .sqlite3
    'experimentBaseName': 'test_multiscan_data',
    # Base filename for multi scan experiment, which will have the scan # appended to it
    'saveFormat': 'sqlite',  # Format to save data. Options are sqlite or json. Sqlite is highly recommended
    'postAnalysis': False,
    # Option to run simple post-scan analysis and plotting: calculate max-min, STA/LTA, and Hilbert Envelope, save plots of data and dump CSVs of the raw metrics
    # NOTE: this is only available if for single or multi scan experiments with saveFormat = 'sqlite'

    ################################################################################
    ####################### Scan Parameters ########################################
    ####### Applies to 'single scan' and 'multi scan' experiment ###################
    ################################################################################

    'primaryAxis': 'X',  # First axis of motion for the scan. 'X' is recommended
    'secondaryAxis': 'Z',  # Second axis of motion for the scan. 'Z' is recommended
    'primaryAxisRange': 150,  # Distance in mm to scan on the primary axis
    'primaryAxisStep': 1,  # Distance in mm between each scan on the primary axis
    'secondaryAxisRange': 25,  # Distance in mm to scan on the secondary axis
    'secondaryAxisStep': -1,  # Distance in mm between each scan on the secondary axis

    ################################################################################
    ################ Repeat Measure Parameters #####################################
    ###### Applies to 'multi scan' and 'repeat pulse' experiments ##################
    ################################################################################

    'scanInterval': 1,  # For multi scans: Minimum time between start of scans, in seconds.
    'numberOfScans': 1,  # For multi scans: Number of times to run the scan
    'pulseInterval': 1,  # For repeat pulse: Minimum time between pulse collection, in seconds
    'experimentTime': 10,  # For repeat pulse: Time to collect data, in seconds

    #################################################################################
    ########################### Sweep Parameters ####################################
    ##################### Applies to 'sweep' experiments ############################
    #################################################################################

    'sweepParams': {  # Dict which defines the parameters to sweep over
        'transducerFrequency': [2.25+i/40 for i in shuffled_arange()]  #   Keys must be other keys of the input params dict
    },  #   Values must be lists of possible values to try for that parameter

    #################################################################################
    ########################## Port Names ###########################################
    ######### Only change if instrument USB ports are changed! ######################
    #################################################################################
    'pulserPort': 'COM15',  # Ultratek pulser port name
    'scannerPort': 'COM6',  # Ender port name
    'dllFile': 'C://USUTSDK//USBUTSDKC//USBUT.dll',
    # Only used for 'pulserType' : 'tone burst'. Location of USBUT350 pulser SDK
    'multiplexerPort': 'COM19',  # Only used if 'multiplexer': True

    ##################################################################################
    ######################### Scanner Size Parameters ################################
    ##################################################################################
    'transducerHolderHeight': 30,  # Z-direction length of the transducer holder, in mm
    'scannerMaxDimensions': (220, 220, 240)  # Maximum dimensions of the scanner.
    # For the Ender-3 or other 3D printers this is the build volume
}


##########################################################################################

##########################################################################################

##########################################################################################
##########################################################################################
####################### END OF USER INPUT ################################################
################# DO NOT CHANGE BELOW THIS LINE ##########################################
##########################################################################################
##########################################################################################

##########################################################################################

##########################################################################################

runExperiment(experimentParams)
