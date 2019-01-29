#!/usr/bin/env python
import sys
from RunFileUtil import RunFileGroups
from ChefUtil import RcdbManager

runStart = int(sys.argv[1])
runEnd = int(sys.argv[2])

rfgs = RunFileGroups()

print 'adding runs ...'
for run in range(runStart,runEnd+1):
  print run
  rfgs.addRun(run)

print 'loading files ...'
for fileName in open('/home/baltzell/clas12/rga/rga-spring-files.txt','r').readlines():
  print fileName
  rfgs.addFile(fileName)

rcdb = RcdbManager()

for run,rfg in rfgs.rfgs.iteritems():
  if rfg.size()>10:
    print run,rfg.size()

print 'checking rcdb ...'
missing=[]
for run in rfgs.getRunList(10):
  try:
    t=rcdb.getTorusScale(run)
    s=rcdb.getSolenoidScale(run)
    r=rcdb.getRunStartTime(run)
  except AttributeError:
    missing.append(run)
print missing


