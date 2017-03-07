import argparse
from datetime import datetime
import itertools
import os
import re
from docker.Container import Container
from docker.ContainerCollection import ContainerCollection
from stats.CpuAcct import CpuAcctStat, CpuAcctPerCore, ThrottledCpu

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output',  help='Name for the output file', required=False,
                        default='ds-' + datetime.now().strftime('%Y-%m-%d')+'.csv')
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
    #print('Result:',  vars(parsed))
    outputFileName =  uniqueFileName(parsed.output)
    print 'Output file: ' + outputFileName
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
            samples.append(collectSample(sampleName, runningContainers))
            sampleNumber += 1
        except EOFError as e:
            break
        finally:
            pass

    with open(outputFileName, 'w') as outputFile:
        for sample in samples:
            cpuacct = sample['cpuacct']
            outputFile.write("{0};{1};{2};{3};{4}\n".format(sample['name'], sample['datetime'],
                             cpuacct.containerName,
                             cpuacct.userJiffies,
                             cpuacct.systemJiffies))

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

def collectSample(sampleName, runningContainers):
    sample = {}
    sample['name'] = sampleName
    sample['datetime'] = datetime.now()
    for container in runningContainers.containers():
        sample['cpuacct'] = CpuAcctStat(container.id, container.name)
        sample['percpu'] =CpuAcctPerCore(container.id, container.name)
        sample['throttled'] = ThrottledCpu(container.id, container.name)
    return sample

if __name__ == "__main__":
    main()
