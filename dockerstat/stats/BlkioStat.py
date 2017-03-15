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
                       (deviceNumber, param, value) = line.split()
                       if not deviceNumber in self.devices:
                           (deviceName, deviceType) = self.deviceName(deviceNumber)
                           self.devices[deviceNumber] = {'name': deviceName, 'type': deviceType, 'bytes': {}, 'operations': {}}
                       self.devices[deviceNumber]['bytes'][param] = value
       except IOError as err:
           if err.errno == ENOENT:
               print("No blkio.throttle.io_service_bytes found for {0}".format(self.containerName))
               pass

       try:
           with open(BlkioStat.blkioPath + self.containerId + "/blkio.throttle.io_serviced", "r") as blkio:
               for line in blkio:
                   if not('Total' in line):
                       (deviceNumber, param, value) = line.split()
                       if not deviceNumber in self.devices:
                           (deviceName, deviceType) = self.deviceName(deviceNumber)
                           self.devices[deviceNumber] = {'name': deviceName, 'type': deviceType, 'bytes': {}, 'operations': {}}
                       self.devices[deviceNumber]['operations'][param] = value
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

   def deviceName(self, deviceNumber):
        sysDevPath = '/sys/dev/block/{0}/uevent'
        deviceName = None
        deviceType = None
        try:
            with open(sysDevPath.format(deviceNumber)) as sysdev:
                for line in sysdev:
                    if 'DEVNAME' in line:
                        (label, deviceName) = line.split('=')
                    if 'DEVTYPE' in line:
                        (label, deviceType) = line.split('=')
        except IOError as err:
            if err.errno == ENOENT:
                print("No {0} found to map device number".format(sysDevPath))
            pass
        return (deviceName, deviceType)