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

pp = pprint.PrettyPrinter(indent=4, width=40, depth=None, stream=None)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',  help='Name for the output files', required=False,
                        default='ds-' + datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
    #print('Result:',  vars(parsed))
    outputFileNameBase =  parsed.output
    print 'Output files: ' + outputFileNameBase + "*.csv"
    cpuSamples = []
    memorySamples = []

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
            sampleNumber += 1
        except EOFError as e:
            break
        finally:
            pass

    outputFileName = uniqueFileName(outputFileNameBase + '-cpu.csv')
    print('\nWriting cpu statistics to {0} ...'.format(outputFileName))
    with open(outputFileName, 'w') as outputFile:
        writeCpuStatisticsHeader(outputFile)
        for cpuSample in cpuSamples:
            writeCpuSample(outputFile, cpuSample)
    outputFile.close()

    outputFileName = uniqueFileName(outputFileNameBase + '-mem.csv')
    print('\nWriting memory statistics to {0} ...'.format(outputFileName))
    with open(outputFileName, 'w') as outputFile:
        writeMemoryStatisticsHeader(outputFile)
        for memorySample in memorySamples:
            writeMemorySample(outputFile, memorySample)
    outputFile.close()

    exit()

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

def writeCpuStatisticsHeader(outputFile):
     outputFile.write("Sample;Timestamp;Container;User Jiffies;System Jiffies;")
     outputFile.write("Enforcement Intervals;Group Throttiling Count;Throttled Time Total;")
     outputFile.write("Cores\n")

def writeCpuSample(outputFile, sample):
    for (container, sampleSet) in sample['containers'].iteritems():
        cpuacct = sampleSet['cpuacct']
        outputFile.write("{0};{1};{2};{3};{4};".format(sample['name'], sample['timestamp'],
                         container,
                         cpuacct.userJiffies,
                         cpuacct.systemJiffies))
        throttled = sampleSet['throttled']
        outputFile.write("{0};{1};{2};".format(throttled.enforcementIntervals,
                                                throttled.groupThrottilingCount,
                                                throttled.throttledTimeTotal))
        outputFile.write("{0}\n".format(sampleSet['percpu'].cpuPerCores()))

def collectMemorySample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['timestamp'] = time()
    sample['containers'] = {}
    for container in runningContainers.containers():
        sample['containers'][container] = MemStat(container.id, container.name)
    return sample

def writeMemoryStatisticsHeader(outputFile):
     outputFile.write("Sample;Timestamp;Container;cache;rss;rss_huge;")
     outputFile.write("mapped_file;dirty;writeback;pgpgin;pgpgout;pgfault;pgmajfault;")
     outputFile.write("inactive_anon;active_anon;inactive_file;active_file;unevictable\n")

def writeMemorySample(outputFile, sample):
    for (container, memStat) in sample['containers'].iteritems():
        memory = memStat.values
        outputFile.write("{0};{1};{2}".format(sample['name'], sample['timestamp'], container.name))
        outputFile.write("{0};{1};{2};{3};{4};{5};{6};{7};{8};{9};".format(
                                            memory['cache'],
                                            memory['rss'],
                                            memory['rss_huge'],
                                            memory['mapped_file'],
                                            memory['dirty'],
                                            memory['writeback'],
                                            memory['pgpgin'],
                                            memory['pgpgout'],
                                            memory['pgfault'],
                                            memory['pgmajfault']))
        outputFile.write("{0};{1};{2};{3};{4}\n".format(
                                            memory['inactive_anon'],
                                            memory['active_anon'],
                                            memory['inactive_file'],
                                            memory['active_file'],
                                            memory['unevictable']))



if __name__ == "__main__":
    main()
