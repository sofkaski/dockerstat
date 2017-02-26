import subprocess
from docker.Container import Container

class ContainerCollection:
    'Class for a collection containers'

    def __init__(self, name=None):
        self._containers = []
        self.name = name

    def getRunningContainers(self):
        self.getContainers(runningOnly=True)

    def getAllContainers(self):
        self.getContainers(runningOnly=False)

    def getContainers(self, runningOnly=False):
        if (runningOnly):
            lines = subprocess.check_output(['docker','ps', '--no-trunc']).splitlines()
        else:
            lines = subprocess.check_output(['docker','ps','-a', '--no-trunc']).splitlines()

        if (len(lines) > 1):
            for line in lines[1:]:
                fields = line.split()
                running = True;
                if (fields[4].find("Exited")):
                    running = False
                container = Container(fields[0], fields[6], image=fields[1], running=running)
                self._containers.append(container)

    def containers(self):
        return self._containers
