import numpy as np
import pickleJar as pj
from matplotlib import pyplot as plt

path = 'C://Users//changlab//Desktop//UT Data//tone burst immersion test//sweep test//'

file = path + 'cycle number sweep.pickle'

# dat = pj.sqliteToPickle(file)
dat = pj.loadPickle(file)

# pj.applyFunctionToData(dat, pj.maxMinusMin, 'amp', ['voltage'])
# dat = pj.applyFunctionToData(dat, np.fft.rfft, 'fft', ['voltage'])
# dat = pj.applyFunctionToData(dat, abs, 'abs_fft', ['fft'])
# #
# timeStep = (dat[0]['time'][1] - dat[0]['time'][0]) / 1000000000
# numSamples = len(dat[0]['time'])
# fft_freq = np.fft.rfftfreq(numSamples, timeStep)
# dat = pj.writeDataToDict(dat, fft_freq, 'fft_freq')

# pj.maxXVal
def findPeakFreq(freq, fft):
    # need to cut off first ~4 points (up to 200kHz) to avoid spurious low f values
    return pj.maxXVal(freq[3:], fft[3:])

# dat = pj.applyFunctionToData(dat, findPeakFreq, 'peak_freq', ['fft_freq', 'abs_fft'])

peakFreq = []
freqs = []

for index in dat.keys():
    if type(index) == int:
        peakFreq.append(dat[index]['peak_freq'])
        freqs.append(index)

plt.plot(freqs,peakFreq)
plt.show()

# for i in  dat.keys():
#     if type(i) == int and i % 2 == 0:
#         plt.plot(dat[i]['fft_freq'], dat[i]['abs_fft'], label = str(i) + 'Half Cycles')
#                  #label = str(0.5 + i/10) + 'MHz')
#         plt.xlim(5e5, 5e6)
#         plt.legend()
#         plt.show()

# plt.show()