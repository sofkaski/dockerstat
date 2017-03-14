import datetime
from errno import ENOENT, EACCES, EPERM
import subprocess
import re

class NetIoStat:
   'Class for net IO metric for a docker container'
   netIoPath = '/proc/{0}/net/dev'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       lines  = subprocess.check_output(['docker','inspect', '-f', '\'{{ .State.Pid }}\'', containerId ])
       self.containerProcess = re.search(r"(\d+)", lines).group(0)
       self.interfaces = {}

       try:
          netIoStatFileName = NetIoStat.netIoPath.format(self.containerProcess)
          with open(netIoStatFileName, "r") as netio:
              for line in netio:
                  elements = line.split()
                  if (len(elements) < 17):
                      continue
                  received = {'bytes': elements[1], 'packets': elements[2]}
                  transmitted = {'bytes': elements[9], 'packets': elements[10]}
                  interface = elements[0].replace(':', '')
                  self.interfaces[interface] = {'received': received, 'transmitted': transmitted}

       except IOError as err:
          if err.errno == ENOENT:
              print("No /net/dev found for {0}".format(self.containerName))
              pass

   def __str__(self):
      result =  "{0} @{1}.\n".format(self.containerName, self.time)
      for interface in self.interfaces.keys():
          received = self.interfaces[interface]['received']
          transmitted = self.interfaces[interface]['transmitted']
          result += "{0}: Received: {1}({2}) Transmitted: {3}({4})\n".format(interface,
                                                                              received['bytes'],
                                                                              received['packets'],
                                                                              transmitted['bytes'],
                                                                              transmitted['packets'])
      return result
