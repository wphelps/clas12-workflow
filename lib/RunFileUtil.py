import os
import re
import glob
import collections

__FILEREGEX='.*clas[_A-Za-z]*_(\d+)\.evio\.(\d+-*\d*)'
__DEBUG=False

def setFileRegex(regex):
  global __FILEREGEX
  print '\nChanging file regex to '+regex+' ... checking for compilation ...'
  re.compile(regex)
  __FILEREGEX = regex

def getFileRegex():
  return __FILEREGEX

def stringToInt(string):
  if string=='':
    return None
  else:
    string=string.lstrip('0')
    if string=='': string='0'
    try:
      return int(string)
    except:
      return None

def getRunFileNumber(fileName):
  mm = re.match(__FILEREGEX,fileName)
  if mm is None:
    if __DEBUG:
      print 'WARNING:  getRunFileNumber Failed on  '+fileName
    return None
  runno=mm.group(1)
  filenos=mm.group(2)
  if filenos.find('-')>0:
    start,end=fileno.split('-')
    filenos=range(stringToInt(start),stringToInt(end)+1)
  else:
    filenos=[stringToInt(filenos)]
  runno=stringToInt(runno)
  return {'run':int(runno),'file':filenos}

class RunFile:
  def __init__(self,fileName):
    self.fileName=None
    self.runNumber=None
    self.fileNumber=None
    if isinstance(fileName,unicode):
      fileName=str(fileName)
    if not type(fileName) is str:
      raise ValueError('fileName must be a string: '+str(fileName))
    fileName=fileName.strip()
    rf=getRunFileNumber(fileName)
    self.fileName=fileName
    if not rf is None:
      self.fileNumber=rf['file']
      self.runNumber=rf['run']
  def __eq__(self,other):
    if not type(other) is type(self): raise TypeError('')
    if self.runNumber != other.runNumber: return False
    if self.fileNumber != other.fileNumber: return False
    return True
  def __lt__(self,other):
    if not type(other) is type(self): raise TypeError('')
    if self.runNumber < other.runNumber: return True
    if self.runNumber > other.runNumber: return False
    if self.fileNumber < other.fileNumber: return True
    if self.fileNumber > other.fileNumber: return False
    return False
  def __gt__(self,other):
    if not type(other) is type(self): raise TypeError('')
    if self.runNumber > other.runNumber: return True
    if self.runNumber < other.runNumber: return False
    if self.fileNumber > other.fileNumber: return True
    if self.fileNumber < other.fileNumber: return False
    return False
  def __str__(self):
    return '%s(%d/%d)'%(self.fileName,self.runNumber,self.fileNumber)
  def show(self):
    print self.fileName,self.runNumber,self.fileNumber

class RunFileGroup(list):
  def __init__(self):
    list.__init__(self)
    self.runNumber=None
  def append(self,rf):
    if not isinstance(rf,RunFile):
      raise TypeError('must be a RunFile')
    elif rf is None or rf.runNumber is None:
      return
    elif self.runNumber is None:
      self.runNumber = rf.runNumber
      list.append(self,rf)
    elif self.runNumber != rf.runNumber:
      raise ValueError('multiple run nubmers ',rf.runNumber)
    elif rf in self:
      raise ValueError('duplicate: ',str(rf))
    else:
      inserted=False
      for ii in range(len(self)):
        if rf < list.__getitem__(self,ii):
          list.insert(self,ii,rf)
          inserted=True
          break
      if not inserted:
        list.append(self,rf)
  def addFile(self,fileName):
    self.append(RunFile(fileName))
  def __str__(self):
    xx=str(self.runNumber)+'('
    xx += ','.join([str(yy.fileNumber) for yy in self])
    xx+=')'
    return xx
  def show(self):
    print str(self.runNumber)
    for rf in self: rf.show()

class RunFileGroups:

  def __init__(self):
    self.combineRuns=False
    self.groupSize=0
    # maintain user's run insertion order:
    self.rfgs=collections.OrderedDict()

  def setCombineRuns(self,val):
    self.combineRuns=val

  def hasRun(self,run):
    return run in self.rfgs

  def addRun(self,run):
    if not type(run) is int:
      raise ValueError('run must be an int: '+str(run))
    self.rfgs[run]=RunFileGroup()

  def addRuns(self,runs):
    for run in runs:
      self.addRun(run)

  def setGroupSize(self,groupSize):
    self.groupSize=int(groupSize)

  def addFile(self,fileName):
    rf=RunFile(fileName)
    # ignore if run# is not registered:
    if rf is None or not rf.runNumber in self.rfgs:
      return
    self.rfgs[rf.runNumber].addFile(fileName)

  def addDir(self,dirName):
    print 'Adding directory '+dirName+' ...'
    for dirpath,dirnames,filenames in os.walk(dirName):
      for filename in filenames:
        self.addFile(dirpath+'/'+filename)

  def findFiles(self,data):

    # recurse if it's a list:
    if isinstance(data,list):
      for datum in data:
        self.findFiles(datum)

    # walk if it's a directory:
    elif os.path.isdir(data):
      self.addDir(data)

    # file containing a file list if it's a file:
    elif os.path.isfile(data):
      for x in open(data,'r').readlines():
        self.addFile(x.split()[0])

    # else assume it's a glob:
    else:
      print 'Assuming '+data+' is a glob.'
      for xx in glob.glob(data):
        if os.path.isdir(xx):
          self.addDir(xx)
        elif os.path.isfile(xx):
          self.addFile(xx)

  def getGroups(self):
    groups=[]
    phaseList=[]
    for run,rfg in self.rfgs.iteritems():
      # make a new group unless we're allowed to combine runs:
      if not self.combineRuns:
        if len(phaseList)>0:
          groups.append(phaseList)
        phaseList=[]
      # loop over the files in this run:
      for rf in rfg:
        phaseList.append(rf.fileName)
        # make a new group if we're over the size limit:
        if self.groupSize>0 and len(phaseList)>=self.groupSize:
          groups.append(phaseList)
          phaseList=[]
    # make a new group for any leftovers:
    if len(phaseList)>0:
      groups.append(phaseList)
    return groups

  def getFlatList(self):
    flatList=[]
    for run,rfg in self.rfgs.iteritems():
      for rf in rfg:
        flatList.append(rf.fileName)
    return flatList

  def getRunList(self,minFileCount=-1):
    runs=[]
    for run,rfg in self.rfgs.iteritems():
      if minFileCount>0 and len(rfg)<minFileCount: continue
      runs.append(run)
    return runs

  def showGroups(self):
    for group in self.getGroups():
      print group

  def showFlatList(self):
    for key,val in self.rfgs.iteritems():
      print key,
      val.show()

  def getFileCount(self):
    return len(self.getFlatList())


