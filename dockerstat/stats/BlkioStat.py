import datetime
from errno import ENOENT, EACCES, EPERM

class BlkioStat:
   'Class for block IO metric for a docker container'
   blkioPath = '/sys/fs/cgroup/blkio/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       self.devices = {}
       try:
           with open(BlkioStat.blkioPath + self.containerId + "/blkio.throttle.io_service_bytes", "r") as blkio:
               for line in blkio:
                   if not('Total' in line):
                       (device, param, value) = line.split()
                       (devMajor,devMinor) = device.split(':')
                       dev = devMajor + '_' + devMinor
                       if not dev in self.devices:
                           self.devices[dev] = {}
                       self.devices[dev]['bytes'] = {param: value}
       except IOError as err:
           if err.errno == ENOENT:
               print("No blkio.throttle.io_service_bytes found for {0}".format(self.containerName))
               pass

       try:
           with open(BlkioStat.blkioPath + self.containerId + "/blkio.throttle.io_serviced", "r") as blkio:
               for line in blkio:
                   if not('Total' in line):
                       (device, param, value) = line.split()
                       (devMajor,devMinor) = device.split(':')
                       dev = devMajor + '_' + devMinor
                       if not dev in self.devices:
                           self.devices[dev] = {} 
                       self.devices[dev]['operations'] = {param: value}
       except IOError as err:
           if err.errno == ENOENT:
               print("No blkio.throttle.io_serviced found for {0}".format(self.containerName))
               pass

   def __str__(self):
      result =  "{0} @{1}.\n".format(self.containerName, self.time)
      for device in self.devices:
          for (param, value) in device['bytes']:
              result += "{0}: {1}: {2}\n".format(device, param, value)
      return result
