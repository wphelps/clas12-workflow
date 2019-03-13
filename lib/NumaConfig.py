#!/usr/bin/env python
import glob,re

# linux only

class NumaConfig:

  _path='/sys/devices/system/node/'
  _maxCpus=1000

  def __init__(self):
    self._nodeMap={}
    self._load()

  # read filesystem and store node/cpu map:
  def _load(self):
    for nodeDir in glob.glob(self._path+'/node*'):
      mm=re.match('.*/node([0-9]+)$',nodeDir)
      if mm is None: continue
      node=int(mm.group(1))
      #if node in self._nodeMap.keys(): continue
      # we found a node, now look for its cpus:
      for cpuDir in glob.glob(nodeDir+'/cpu*'):
        mm=re.match('.*/cpu([0-9]+)$',cpuDir)
        if mm is None: continue
        cpu=int(mm.group(1))
        # we found a cpu, add the node to the map if necessary:
        if node not in self._nodeMap:
          self._nodeMap[node]=[]
        #if cpu in self._nodeMap[node]: continue
        # we found a new cpu for this node, insert it in order:
        inserted=False
        for ii in range(len(self._nodeMap[node])):
          if cpu < self._nodeMap[node][ii]:
            self._nodeMap[node].insert(ii,cpu)
        if not inserted:
          self._nodeMap[node].append(cpu)

  # return cpu mask for a node:
  def mask(self,node):
    mask=0x0
    for cpu in self._nodeMap[node]:
      mask |= (1<<cpu)
    return mask

  # return list of nodes:
  def nodes(self):
    return sorted(self._nodeMap.keys())

  # return list of all cpus on a node:
  def cpus(self,node):
    cpus=[]
    for cg in self.cpuGroups(node):
      cpus.extend(cg)
    return cpus

  # return lists of consecutive cpus on a node:
  def cpuGroups(self,node):
    groups=[]
    for ii in range(self._maxCpus):
      if ii in self._nodeMap[node]:
        if len(groups)>0:
          lenPrevious = len(groups[len(groups)-1])
          previous = groups[len(groups)-1][lenPrevious-1]
          if ii-previous==1:
            groups[len(groups)-1].append(ii)
          else:
            groups.append([ii])
        else:
          groups.append([ii])
    return groups

  # return pretty cli argument for `taskset -c` command:
  def tasksetArg(self,node):
    groups=[]
    for group in self.cpuGroups(node):
      if len(group)==1:
        groups.append(str(group[0]))
      elif len(groups)==2:
        groups.append(str(group[0])+','+str(group[1]))
      else:
        groups.append(str(group[0])+'-'+str(group[len(group)-1]))
    return ','.join(groups)

if __name__ == '__main__':
  nc=NumaConfig()
  for node in nc.nodes():
    print node,'%3d'%len(nc.cpus(node)),nc.tasksetArg(node)
    print '%22s'%('0x%x'%nc.mask(node)),
    for cpu in nc.cpus(node): print '%.2d'%cpu,
    print

