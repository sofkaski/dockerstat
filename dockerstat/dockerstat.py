import argparse
from docker.Container import Container
from docker.ContainerCollection import ContainerCollection
from stats.CpuAcct import CpuAcctStat, CpuAcctPerCore, ThrottledCpu

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
        cpuacct = CpuAcctStat(container.id, container.name)
        print cpuacct
        percpu =CpuAcctPerCore(container.id, container.name)
        print percpu
        throttled = ThrottledCpu(container.id, container.name)
        print throttled



if __name__ == "__main__":
    main()
