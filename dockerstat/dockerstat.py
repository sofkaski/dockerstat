import argparse
from datetime import datetime
from time import time
import itertools
import os
import re
from sys import exit
from docker.Container import Container
from docker.ContainerCollection import ContainerCollection
from stats.CpuAcct import CpuAcctStat, CpuAcctPerCore, ThrottledCpu

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',  help='Name for the output files', required=False,
                        default='ds-' + datetime.now().strftime('%Y-%m-%d'))
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
    #print('Result:',  vars(parsed))
    outputFileNameBase =  parsed.output
    print 'Output files: ' + outputFileNameBase + "*.csv"
    samples = []

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
            sample = collectCpuSample(sampleName, runningContainers)
            samples.append(sample)
            sampleNumber += 1
        except EOFError as e:
            break
        finally:
            pass

    outputFileName = uniqueFileName(outputFileNameBase + '-cpu.csv')
    print('\nWriting cpu statistics to {0} ...'.format(outputFileName))
    with open(outputFileName, 'w') as outputFile:
        writeCpuStatisticsHeader(outputFile)
        for sample in samples:
            writeCpuSample(outputFile, sample)
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
    for container in runningContainers.containers():
        sample['cpuacct'] = CpuAcctStat(container.id, container.name)
        sample['percpu'] = CpuAcctPerCore(container.id, container.name)
        sample['throttled'] = ThrottledCpu(container.id, container.name)
    return sample

def writeCpuStatisticsHeader(outputFile):
     outputFile.write("Sample;Timestamp;Container;User Jiffies;System Jiffies;")
     outputFile.write("Enforcement Intervals;Group Throttiling Count;Throttled Time Total;")
     outputFile.write("Cores\n")

def writeCpuSample(outputFile, sample):
    cpuacct = sample['cpuacct']
    outputFile.write("{0};{1};{2};{3};{4};".format(sample['name'], sample['timestamp'],
                     cpuacct.containerName,
                     cpuacct.userJiffies,
                     cpuacct.systemJiffies))
    throttled = sample['throttled']
    outputFile.write("{0};{1};{2};".format(throttled.enforcementIntervals,
                                            throttled.groupThrottilingCount,
                                            throttled.throttledTimeTotal))
    outputFile.write("{0}\n".format(sample['percpu'].cpuPerCores()))

if __name__ == "__main__":
    main()
