import datetime

class CpuAcct:
   'Class for cpu metric for a docker container'
   cpuacctPath = '/sys/fs/cgroup/cpuacct/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       with open(CpuAcct.cpuacctPath + self.containerId + "/cpuacct.stat", "r") as cpuacct:
           for line in cpuacct:
               fields = line.split()
               if (fields[0].find('user')):
                   self.userJiffies = fields[1]
               if (fields[0].find('system')):
                   self.systemJiffies = fields[1]

   def __str__(self):
        return "{0} @{1}. User={2} System={3} (in jiffies)".format(self.containerName, self.time, self.userJiffies, self.systemJiffies)

   def __unicode__(self):
        return u"{0} @{1}. User={2} System={3} (in jiffies)".format(self.containerName, self.time, self.userJiffies, self.systemJiffies)
