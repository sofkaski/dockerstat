import argparse
from docker.Container import Container
from docker.ContainerCollection import ContainerCollection
from stats.CpuAcct import CpuAcct

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cpu',  help='Collect CPU statistics', required=False, default=True)
    parser.add_argument('arg', nargs='*') # use '+' for 1 or more args (instead of 0 or more)
    parsed = parser.parse_args()
#    print('Result:',  vars(parsed))

    runningContainers = ContainerCollection()
    runningContainers.getRunningContainers()
    print('Found {0} running containers'.format(len(runningContainers.containers())))
    allContainers = ContainerCollection()
    allContainers.getAllContainers()
    print('Found total {0} containers'.format(len(allContainers.containers())))
    for container in runningContainers.containers():
        cpuacct = CpuAcct(container.id, container.name)
        print cpuacct



if __name__ == "__main__":
    main()
