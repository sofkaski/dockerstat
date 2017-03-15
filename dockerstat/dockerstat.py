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
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
    #print('Result:',  vars(parsed))
    global outputFileNameBase
    outputFileNameBase =  parsed.output
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

    writeStatistics('cpu', cpuSamples, writeCpuStatisticsHeader, writeCpuSample)
    writeStatistics('mem', memorySamples, writeMemoryStatisticsHeader, writeMemorySample)
    writeStatistics('blkio', blkioSamples, writeBlkioStatisticsHeader, writeBlkioSample)
    writeStatistics('netio', netioSamples, writeNetioStatisticsHeader, writeNetioSample)

    exit()

def writeStatistics(statisticsType, samples, headerFunction, sampleWriteFunction):
    outputFileName = uniqueFileName(outputFileNameBase + '-' + statisticsType + '.csv')
    print('\nWriting {0} statistics to {1} ...'.format(statisticsType, outputFileName))
    with open(outputFileName, 'w') as outputFile:
        headerNotWritten = True
        for sample in samples:
            if headerNotWritten:
                headerFunction(outputFile, sample)
                headerNotWritten = False
            sampleWriteFunction(outputFile, sample)
    outputFile.close()

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
        sampleSet['percpu'] = CpuAcctPerCore(container.id, container.name)
        sampleSet['throttled'] = ThrottledCpu(container.id, container.name)
        sample['containers'][container.name] = sampleSet
    # pp.pprint(sample)
    return sample

def writeCpuStatisticsHeader(outputFile,sample):
     outputFile.write("Sample;Timestamp;Container;User Jiffies;System Jiffies;")
     outputFile.write("Enforcement Intervals;Group Throttiling Count;Throttled Time Total;")
     outputFile.write("Cores\n")

def writeCpuSample(outputFile, sample):
    for (container, sampleSet) in sample['containers'].iteritems():
        cpuacct = sampleSet['cpuacct']
        userJiffies = getattr(cpuacct, 'userJiffies', None)
        systemJiffies = getattr(cpuacct, 'systemJiffies', None)
        outputFile.write("{0};{1};{2};{3};{4};".format(sample['name'], sample['timestamp'],
                         container,
                         userJiffies,
                         systemJiffies))
        throttled = sampleSet['throttled']
        enforcementIntervals = getattr(throttled, 'enforcementIntervals', None)
        groupThrottilingCount = getattr(throttled, 'groupThrottilingCount', None)
        throttledTimeTotal = getattr(throttled, 'throttledTimeTotal', None)
        outputFile.write("{0};{1};{2};".format(enforcementIntervals,
                                               groupThrottilingCount,
                                               throttledTimeTotal))
        outputFile.write("{0}\n".format(sampleSet['percpu'].cpuPerCores()))

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

def writeMemorySample(outputFile, sample):
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
     outputFile.write("Sample;Timestamp;Container;Device;Operation;Count;Bytes\n")

def writeBlkioSample(outputFile, sample):
    for (container, blkioSample) in sample['containers'].iteritems():
        blkioDevices = blkioSample.devices
        for device in blkioDevices:
            for operation in ('Read', 'Write', 'Async', 'Sync'):
                ops = None
                bytes = None
                if operation in blkioDevices[device]['operations']:
                    ops = blkioDevices[device]['operations'][operation]
                if operation in blkioDevices[device]['bytes']:
                    bytes = blkioDevices[device]['bytes'][operation]
                outputFile.write("{0};{1};{2};".format(sample['name'], sample['timestamp'], container.name))
                outputFile.write("{0};{1};{2};{3}\n".format(device, operation, ops, bytes))

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

def writeNetioSample(outputFile, sample):
    for (container, netioSample) in sample['containers'].iteritems():
        interfaces = netioSample.interfaces
        for interface in interfaces.keys():
            outputFile.write("{0};{1};{2};".format(sample['name'], sample['timestamp'], container.name))
            received = interfaces[interface]['received']
            transmitted = interfaces[interface]['transmitted']
            outputFile.write("{0};{1};{2};{3};{4}\n".format(interface,
                                                            received['bytes'],
                                                            received['packets'],
                                                            transmitted['bytes'],
                                                            transmitted['packets']))


if __name__ == "__main__":
    main()
