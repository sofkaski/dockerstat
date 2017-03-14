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

       try:
          netIoStatFileName = NetIoStat.netIoPath.format(self.containerProcess)
          print netIoStatFileName
          with open(netIoStatFileName, "r") as netio:
              for line in netio:
                  print line

       except IOError as err:
          if err.errno == ENOENT:
              print("No /net/dev found for {0}".format(self.containerName))
              pass

   def __str__(self):
      result =  "{0} @{1}.\n".format(self.containerName, self.time)

      return result
