import json
import picosdkRapidblockPulse as pico
import ultratekPulser as pulser
import time
import tqdm
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


def repeatPulse(params):

    # Connect to picoscope, ender, pulser
    picoConnection = pico.openPicoscope()
    pulserConnection = pulser.openPulser(params['pulserPort'])

    # generate filename for current scan json
    scanFileName = params['experimentFolder'] + params['experimentName']

    # Set up plot
    plt.ion()
    figure, ax = plt.subplots()

    wavePlot, = ax.plot([1,2], [1,2])
    plt.xlabel('Time (ns)')
    plt.ylabel('Intensity (mV)')
    plt.title('Initializing plot')

    # Setup picoscope
    picoConnection = pico.setupPicoMeasurement(picoConnection,
                                               params['measureDelay'],
                                               params['voltageRange'],
                                               params['samples'],
                                               params['measureTime'])

    # Turn on pulser
    pulser.pulserOn(pulserConnection)

    # initialize time
    experimentTime = params['experimentTime']
    startTime = time.time()
    endTime = startTime + experimentTime

    # initialize progress bar
    pbar = tqdm.tqdm(total=experimentTime)

    #start pulse collection loop. Run until end of experiment
    while time.time() < endTime:

        # record scan start time
        pulseStartTime = time.time()

        # collect data
        waveform = pico.runPicoMeasurement(picoConnection, params['waves'])

        # Plot the data
        wavePlot.set_xdata(waveform[1])
        wavePlot.set_ydata(waveform[0])

        #draw updated plot
        figure.canvas.draw()
        figure.canvas.flush_events()

        # Make data pretty for json
        waveformList = []
        waveformList.append(list(waveform[0]))
        waveformList.append(list(waveform[1]))

        timeString = "Time: " + str(time.time())

        metaDataList = [timeString]

        # #clear old plot and plot current data
        # plt.plot(waveform[0], waveform[1])
        # plt.show()

        # write data
        with open(scanFileName, 'a') as file:
            json.dump(waveformList, file)
            file.write('\n')
            json.dump(metaDataList, file)
            file.write('\n')

        # calculate time elapsed in this iteration
        iterationTime = time.time() - pulseStartTime

        # check difference between iteration time and experiment pulse interval
        waitTime = params['pulseInterval'] - iterationTime

        # If time spent on iteration is less than pulseInterval, wait until pulseInterval has elapsed
        if waitTime > 0:
            time.sleep(waitTime)

            #update progress bar
            pbar.update(params['pulseInterval'])

        # iterationTime is longer than pulse interval. Immediately repeat the iteration and update pbar the correct amount
        else:
            pbar.update(iterationTime)

    pbar.close()

    pulser.pulserOff(pulserConnection)
    pico.closePicoscope(picoConnection)