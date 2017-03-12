import datetime
from errno import ENOENT, EACCES, EPERM

class MemStat:
   'Class for memorystatistics for a docker container'
   memoryPath = '/sys/fs/cgroup/memory/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       self.values = {}
       try:
           with open(MemStat.memoryPath + self.containerId + "/memory.stat", "r") as memstat:
               for line in memstat:
                   (param, value) = line.split()
                   self.values[param] = value
       except IOError as err:
           if err.errno == ENOENT:
               print("No memory.stat found for {0}".format(self.containerName))
               pass

   def __str__(self):
       result =  "{0} @{1}.\n".format(self.containerName, self.time)
       for (param, value) in self.values:
         result += "{0}: {1}\n".format(param, value)
       return result
