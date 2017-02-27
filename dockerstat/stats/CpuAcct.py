import datetime

class CpuAcctStat:
   'Class for cpu metric for a docker container'
   cpuacctPath = '/sys/fs/cgroup/cpuacct/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       with open(CpuAcctStat.cpuacctPath + self.containerId + "/cpuacct.stat", "r") as cpuacct:
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

class CpuAcctPerCore:
   'Class for cpu per core metric for a docker container'
   cpuacctPath = '/sys/fs/cgroup/cpuacct/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       self.perCore = []
       with open(CpuAcctPerCore.cpuacctPath + self.containerId + "/cpuacct.usage_percpu", "r") as cpuacct:
           for line in cpuacct:
               fields = line.split()
               for core in fields:
                   self.perCore.append(core)

   def cpuPerCores(self):
       cpu = ''
       for i, core in enumerate(self.perCore):
           if (i):
               cpu += ',' + core
           else:
               cpu += core
       return cpu

   def __str__(self):
        return "{0} @{1}. CPU (ns per core): {2}".format(self.containerName, self.time, self.cpuPerCores())

   def __unicode__(self):
        return u"{0} @{1}. CPU (ns per core): {2}".format(self.containerName, self.time, self.cpuPerCores())

class ThrottledCpu:
   'Class for cpu throttling for a docker container'
   cpuacctPath = '/sys/fs/cgroup/cpuacct/docker/'

   def __init__(self, containerId, containerName):
       self.containerId = containerId
       self.containerName = containerName
       self.time = datetime.datetime.now()
       self.perCore = []
       with open(CpuAcctPerCore.cpuacctPath + self.containerId + "/cpu.stat", "r") as cpuacct:
           for line in cpuacct:
              fields = line.split()
              if (fields[0].find('nr_periods')):
                  self.enforcementIntervals = fields[1]
              if (fields[0].find('nr_throttled')):
                  self.groupThrottilingCount = fields[1]
              if (fields[0].find('throttled_time')):
                  self.throttledTimeTotal = fields[1]

   def __str__(self):
        return "{0} @{1}. EnforcementIntervals={2} GroupThrottilingCount={3} ThrottledTimeTotal={4}"\
                .format(self.containerName, self.time, self.enforcementIntervals, self.groupThrottilingCount,self.throttledTimeTotal)

   def __unicode__(self):
        return u"{0} @{1}. EnforcementIntervals={2} GroupThrottilingCount={3} ThrottledTimeTotal={4} (ns)"\
                .format(self.containerName, self.time, self.enforcementIntervals, self.groupThrottilingCount,self.throttledTimeTotal)
