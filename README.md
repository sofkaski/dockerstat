# dockerstat
Python scripts to aid collection of docker containers resource consumption statistics in Linux hosts.
## installation
Clone the repo or unzip tar file to some directory
## Running
```
python dockerstat.py [-o | --output <output file name>]
```
--output option can be used to give a basic name for output files. The default name is ds-&lt;date&gt;.

When running the script asks repeatedly for a sample name. You can use the name of the use case that you are testing.
Sample name can be left empty and then default sample name is used.
Default is Sample_0, Sample_1, ...

When sample name, or empty, is given the script takes a sample of docker resources from all running docker containers.
This can be repeated as many times as wanted.
Once through with testing hit ctrl-d and then the script will output four files to working directory: cpu, memory, block io and net io statistics.  
## Produced data files
Files are csv formatted and can be opened e.g. with excel.
Example file set from a run :
 * ds-2017-03-14-blkio.csv  
 * ds-2017-03-14-cpu.csv  
 * ds-2017-03-14-mem.csv  
 * ds-2017-03-14-netio.csv

Script will add postfixes to names to produce unique file names,
if subsequent runs are made using the same basic name for output files.

There is a header line and row for each sample, including timestamp.

For more information about data content see e.g [Data Dog blog](https://www.datadoghq.com/blog/how-to-collect-docker-metrics/) about docker metrics.
