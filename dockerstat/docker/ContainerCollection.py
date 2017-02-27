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
        formatString = '{{.ID}};{{.Names}};{{.Image}};{{.Status}}'
        if (runningOnly):
            lines = subprocess.check_output(['docker','ps', '--no-trunc', '--format', formatString ]).splitlines()
        else:
            lines = subprocess.check_output(['docker','ps','-a', '--no-trunc', '--format', formatString ]).splitlines()

        if (len(lines) > 0):
            for line in lines:
                fields = line.split(';')
                if (len(fields) < 4):
                    next
                running = True;
                if (fields[2].find("Exited")):
                    running = False
                container = Container(fields[0], fields[1], image=fields[2], running=running)
                self._containers.append(container)

    def containers(self):
        return self._containers
