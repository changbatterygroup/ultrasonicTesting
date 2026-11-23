import ultrasonicScan as scan
import multiscan
import scanSetupFunctions as setup
import repeatPulse
import gui

# Function to choose experiment function based on parameters
def runExperiment(params: dict):
    if params['gui']:
        gui.startGUI(params)

    else:
        # get the experiment from the input
        experiment = params['experiment']

        #run the appropriate experiment function
        # 'move' = move the transducers
        # 'single pulse' = perform a single test pulse
        # 'single scan' = perform a single 2D scan
        # 'multi scan' = repeat a 2D scan with a set frequency
        match experiment:
            case 'move':
                setup.moveScanner(params)

            case 'single pulse':
                setup.singlePulseMeasure(params)

            case 'repeat pulse':
                repeatPulse.repeatPulse(params)

            case 'sweep':
                repeatPulse.sweepParameters(params, params['sweepParams'])

            case 'single scan':
                scan.runScan(params)

            case 'multi scan':
                multiscan.multiscan(params)

            #Match case where no matching expiment is input
            case _:
                print(
                    "No experiment matches input. Check the value of the 'experiment' parameter and ensure it is a valid experiment")
                print("Valid experiments are: 'move', 'single pulse', 'single scan', and 'multi scan'")

