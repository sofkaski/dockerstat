import argparse
from datetime import datetime
from time import time
import itertools
import os
import re
import pprint
from sys import exit
from docker.Container import Container
from docker.ContainerCollection import ContainerCollection
from stats.CpuAcct import CpuAcctStat, CpuAcctPerCore, ThrottledCpu
from stats.MemStat import MemStat
from stats.BlkioStat import BlkioStat
from stats.NetIoStat import NetIoStat

pp = pprint.PrettyPrinter(indent=4, width=40, depth=None, stream=None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',  help='Name for the output files', required=False,
                        default='ds-' + datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('-d', '--delta',  help='Calculate and output deltas between samples', required=False,
                        action='store_true')
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
    #print('Result:',  vars(parsed))
    global outputFileNameBase
    outputFileNameBase =  parsed.output
    calculateDeltas = parsed.delta
    print 'Output files: ' + outputFileNameBase + "*.csv"
    cpuSamples = []
    memorySamples = []
    blkioSamples = []
    netioSamples = []

    runningContainers = ContainerCollection()
    runningContainers.getRunningContainers()
    print('Found {0} running containers'.format(len(runningContainers.containers())))
    allContainers = ContainerCollection()
    allContainers.getAllContainers()
    print('Found total {0} containers'.format(len(allContainers.containers())))

    sampleNumber = 0
    while (True):
        sampleName = "Sample_" + str(sampleNumber)
        try:
            tmp = raw_input('Next sample? (ctrl-d to exit) [' + sampleName + ']: ')
            if tmp != '':
                sampleName = tmp
            cpuSample = collectCpuSample(sampleName, runningContainers)
            cpuSamples.append(cpuSample)
            memorySample = collectMemorySample(sampleName, runningContainers)
            memorySamples.append(memorySample)
            blkioSample = collectBlkioSample(sampleName, runningContainers)
            blkioSamples.append(blkioSample)
            netioSample = collectNetioSample(sampleName, runningContainers)
            netioSamples.append(netioSample)
            sampleNumber += 1
        except EOFError as e:
            break
        finally:
            pass

    if calculateDeltas:
        if len(cpuSamples) < 2:
            print('\nAt least two samples are needed when deltas are calculated.')
            return

    writeStatistics('cpu', cpuSamples, writeCpuStatisticsHeader, writeCpuSample, calculateDeltas)
    writeStatistics('mem', memorySamples, writeMemoryStatisticsHeader, writeMemorySample, calculateDeltas)
    writeStatistics('blkio', blkioSamples, writeBlkioStatisticsHeader, writeBlkioSample, calculateDeltas)
    writeStatistics('netio', netioSamples, writeNetioStatisticsHeader, writeNetioSample, calculateDeltas)

    exit()

def writeStatistics(statisticsType, samples, headerFunction, sampleWriteFunction, calculateDeltas):
    outputFileName = uniqueFileName(outputFileNameBase + '-' + statisticsType + '.csv')
    if calculateDeltas:
        print('\nWriting sample deltas of {0} statistics to {1} ...'.format(statisticsType, outputFileName))
    else:
        print('\nWriting {0} statistics to {1} ...'.format(statisticsType, outputFileName))
    with open(outputFileName, 'w') as outputFile:
        headerNotWritten = True
        prevSample = None
        for sample in samples:
            if headerNotWritten:
                headerFunction(outputFile, sample)
                headerNotWritten = False
            if calculateDeltas:
                if prevSample == None:
                    prevSample = sample
                    continue
                sampleWriteFunction(outputFile, sample, prevSample)
                prevSample = sample
            else:
                sampleWriteFunction(outputFile, sample, None)

def uniqueFileName(file):
    '''Append counter to the end of filename body, if the file already exists'''
    if not os.path.isfile(file):
        return file
    if re.match('.+\.[a-zA-Z0-9]+$', os.path.basename(file)):
        name_func = lambda f, i: re.sub('(\.[a-zA-Z0-9]+)$', '_%i\\1' % i, f)
    else:
        name_func = lambda f, i: ''.join([f, '_%i' % i])
    for new_file_name in (name_func(file, i) for i in itertools.count(1)):
        if not os.path.exists(new_file_name):
            return new_file_name

def collectCpuSample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['timestamp'] = time()
    sample['containers'] = {}
    for container in runningContainers.containers():
        sampleSet = {}
        sampleSet['cpuacct'] = CpuAcctStat(container.id, container.name)
        sampleSet['percore'] = CpuAcctPerCore(container.id, container.name)
        sampleSet['throttled'] = ThrottledCpu(container.id, container.name)
        sample['containers'][container.name] = sampleSet
    # pp.pprint(sample)
    return sample

def writeCpuStatisticsHeader(outputFile,sample):
     outputFile.write("Sample;Timestamp;Container;User Jiffies;System Jiffies;")
     outputFile.write("Enforcement Intervals;Group Throttiling Count;Throttled Time Total;")
      # Pick first container and  first sample and nbr of cores from there
     firstContainer = sample['containers'].keys()[0]
     perCoreSample = sample['containers'][firstContainer]['percore']
     for i in range(0,len(perCoreSample.perCore)):
        outputFile.write("Core {0};".format(i))
     outputFile.write("\n")

def writeCpuSample(outputFile, sample, prevSample):
    for (container, sampleSet) in sample['containers'].iteritems():
        cpuacct = sampleSet['cpuacct']
        userJiffies = number(getattr(cpuacct, 'userJiffies', None))
        systemJiffies = number(getattr(cpuacct, 'systemJiffies', None))
        if prevSample:
            prevCpuacct = prevSample['containers'][container]['cpuacct']
            prevUserJiffies = number(getattr(prevCpuacct, 'userJiffies', None))
            prevSystemJiffies = number(getattr(prevCpuacct, 'systemJiffies', None))
            if prevUserJiffies:
                userJiffies -= prevUserJiffies
            if prevSystemJiffies:
                systemJiffies -= prevSystemJiffies
        outputFile.write("{0};{1};{2};{3};{4};".format(sample['name'], sample['timestamp'],
                         container,
                         userJiffies,
                         systemJiffies))
        throttled = sampleSet['throttled']
        enforcementIntervals = number(getattr(throttled, 'enforcementIntervals', None))
        groupThrottilingCount = number(getattr(throttled, 'groupThrottilingCount', None))
        throttledTimeTotal = number(getattr(throttled, 'throttledTimeTotal', None))
        if prevSample:
            prevThrottled = prevSample['containers'][container]['throttled']
            prevEnforcementIntervals = number(getattr(prevThrottled, 'enforcementIntervals', None))
            prevGroupThrottilingCount = number(getattr(prevThrottled, 'groupThrottilingCount', None))
            prevThrottledTimeTotal = number(getattr(prevThrottled, 'throttledTimeTotal', None))
            if prevEnforcementIntervals:
                enforcementIntervals -= prevEnforcementIntervals
            if prevGroupThrottilingCount:
                groupThrottilingCount -= prevGroupThrottilingCount
            if prevThrottledTimeTotal:
                throttledTimeTotal -= prevThrottledTimeTotal
        outputFile.write("{0};{1};{2}".format(enforcementIntervals,
                                               groupThrottilingCount,
                                               throttledTimeTotal))
        perCoreSample = sampleSet['percore']
        prevPerCoreSample = None
        if prevSample:
            prevPerCoreSample = prevSample['containers'][container]['percore']
        for i, coreNs in enumerate(perCoreSample.perCore):
            ns = number(coreNs)
            if prevPerCoreSample:
                ns -= number(prevPerCoreSample.perCore[i])
            outputFile.write(";{0}".format(ns))
        outputFile.write("\n")

def collectMemorySample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['timestamp'] = time()
    sample['containers'] = {}
    for container in runningContainers.containers():
        sample['containers'][container] = MemStat(container.id, container.name)
    return sample

def writeMemoryStatisticsHeader(outputFile, sample):
    outputFile.write("Sample;Timestamp;Container")
     # Take rest of the headers from sample. Content of memory statistics seem to vary in different versions
     # Pick first container and  first sample
    firstContainer = sample['containers'].keys()[0]
    memSample = sample['containers'][firstContainer]
    for key in sorted(memSample.values.keys()):
        outputFile.write(";{0}".format(key))
    outputFile.write("\n")

def writeMemorySample(outputFile, sample, prevSample):
    for (container, memStat) in sample['containers'].iteritems():
        outputFile.write("{0};{1};{2}".format(sample['name'], sample['timestamp'], container.name))
        for key in sorted(memStat.values.keys()):
            outputFile.write(";{0}".format(memStat.values[key]))
        outputFile.write("\n")

def collectBlkioSample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['timestamp'] = time()
    sample['containers'] = {}
    for container in runningContainers.containers():
        sample['containers'][container] = BlkioStat(container.id, container.name)
    return sample

def writeBlkioStatisticsHeader(outputFile, sample):
     outputFile.write("Sample;Timestamp;Container;Device;Read count;Write count;Async count;Sync count;Read bytes;Write bytes;Async bytes;Sync bytes;\n")

def writeBlkioSample(outputFile, sample, prevSample):
    for (container, blkioSample) in sample['containers'].iteritems():
        blkioDevices = blkioSample.devices
        prevBlkioDevices = None
        if prevSample:
            prevBlkioDevices = prevSample['containers'][container].devices

        for device in blkioDevices:
            outputFile.write("{0};{1};{2};".format(sample['name'], sample['timestamp'], container.name))
            outputFile.write("{0}({1})".format(blkioDevices[device]['name'], blkioDevices[device]['type']))
            for operation in ('Read', 'Write', 'Async', 'Sync'):
                value = number(blkioDevices[device]['operations'][operation])
                if prevBlkioDevices:
                    value -= number(prevBlkioDevices[device]['operations'][operation])
                outputFile.write(";{0}".format(value))
            for operation in ('Read', 'Write', 'Async', 'Sync'):
                value = number(blkioDevices[device]['bytes'][operation])
                if prevBlkioDevices:
                    value -= number(prevBlkioDevices[device]['bytes'][operation])
                outputFile.write(";{0}".format(value))
            outputFile.write("\n")

def collectNetioSample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['timestamp'] = time()
    sample['containers'] = {}
    for container in runningContainers.containers():
        sample['containers'][container] = NetIoStat(container.id, container.name)
    return sample

def writeNetioStatisticsHeader(outputFile, sample):
     outputFile.write("Sample;Timestamp;Container;Interface;Received bytes;Received packets;Sent bytes;Sent packets\n")

def writeNetioSample(outputFile, sample, prevSample):
    for (container, netioSample) in sample['containers'].iteritems():
        interfaces = netioSample.interfaces
        prevInterfaces = None
        if prevSample:
            prevInterfaces = prevSample['containers'][container].interfaces
        for interface in interfaces.keys():
            outputFile.write("{0};{1};{2};".format(sample['name'], sample['timestamp'], container.name))
            receivedBytes = number(interfaces[interface]['received']['bytes'])
            transmittedBytes = number(interfaces[interface]['transmitted']['bytes'])
            receivedPackets = number(interfaces[interface]['received']['packets'])
            transmittedPackets = number(interfaces[interface]['transmitted']['packets'])
            if prevInterfaces:
                receivedBytes -= number(prevInterfaces[interface]['received']['bytes'])
                transmittedBytes -= number(prevInterfaces[interface]['transmitted']['bytes'])
                receivedPackets -= number(prevInterfaces[interface]['received']['packets'])
                transmittedPackets = number(prevInterfaces[interface]['transmitted']['packets'])
                
            outputFile.write("{0};{1};{2};{3};{4}\n".format(interface,
                                                            receivedBytes,
                                                            receivedPackets,
                                                            transmittedBytes,
                                                            transmittedPackets))

def number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)
    except TypeError:
        return None

if __name__ == "__main__":
    main()
