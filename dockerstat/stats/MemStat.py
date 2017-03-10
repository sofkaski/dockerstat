import datetime

class MemStat:
   'Class for memorystatistics for a docker container'
   memoryPath = '/sys/fs/cgroup/memory/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       self.values = {}
       with open(MemStat.memoryPath + self.containerId + "/memory.stat", "r") as memstat:
           for line in memstat:
               (param, value) = line.split()
               self.values[param] = value

   def __str__(self):
       result =  "{0} @{1}.\n".format(self.containerName, self.time)
       for (param, value) in self.values:
         result += "{0}: {1}\n".format(param, value)
       return result
