import numpy as np
import pickleJar as pj
from matplotlib import pyplot as plt
from scipy.signal import butter, sosfiltfilt
# 'experimentFolder': 'C://Users//changlab//Desktop//UT Data//temperature testing//',
# Name of folder to dump data "C:\Users\changlab\Desktop\UT Data"
path = 'C://Users//changlab//Desktop//UT Data//TMM_SS_characterization//'
# file_ = 'test_water_resonance.sqlite3'
file_ = f'short_rods_echo_steel_steel'
file = path + file_ + '.pickle'

dat_ = pj.sqliteToPickle(path+file_+'.sqlite3')
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
# def findPeakFreq(freq, fft):
#     # need to cut off first ~4 points (up to 200kHz) to avoid spurious low f values
#     return pj.maxXVal(freq[3:], fft[3:])
#
# # dat = pj.applyFunctionToData(dat, findPeakFreq, 'peak_freq', ['fft_freq', 'abs_fft'])

# data = np.array([dat[ind]['voltage'] for ind in range(len(dat)-2)]).sum(axis=0)

data = np.array([dat[ind]['voltage'] for ind in range(len(dat)-2)]).sum(axis=0)

dt = (dat[0]['time'][1] - dat[0]['time'][0]) * 1e-9
f_s = 1 / dt
sos = butter(3, [f_s / 250, f_s / 5], btype="bandpass", fs=f_s, output="sos")

filtered = sosfiltfilt(sos, data)

plt.plot(dat[0]['time'], filtered, label='f')

# forward = np.array([dat[ind]['voltage_echo_forward'] for ind in range(10)]).sum(axis=0)
# reverse = np.array([dat[ind]['voltage_echo_reverse'] for ind in range(10)]).sum(axis=0)
#
# plt.plot(dat[0]['time'], forward, label='f')
# plt.plot(dat[0]['time'], reverse, label='r')
plt.legend()

# peakFreq = []
# freqs = []

# print(dat.keys())
# for index in dat.keys():
#     if type(index) == int:
#         waves.append(dat[index][])
#         freqs.append(index)
#
# plt.plot(freqs,peakFreq)
plt.show()

# for i in  dat.keys():
#     if type(i) == int and i % 2 == 0:
#         plt.plot(dat[i]['fft_freq'], dat[i]['abs_fft'], label = str(i) + 'Half Cycles')
#                  #label = str(0.5 + i/10) + 'MHz')
#         plt.xlim(5e5, 5e6)
#         plt.legend()
#         plt.show()

# plt.show()