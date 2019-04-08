import os
import sys
import json
import copy
import argparse
import traceback

import ChefUtil
import RunFileUtil
import CLAS12Workflows

RUNGROUPS=['rga','rgb','rgk','rgm','rgl','rgd','rge','test']
TRACKS=['reconstruction','debug']
TASKS=['decode','recon']
MODELS=[0,1,2,3]
CFG={
    'project'       : 'clas12',
    'track'         : 'reconstruction',
    'task'          : 'decode',
    'runGroup'      : None,
    'coatjava'      : '/group/clas12/packages/coatjava-6b.0.0',
    'tag'           : None,
    'inputs'        : [],
    'runs'          : [],
    'workDir'       : None,
    'outDir'        : None,
    'phaseSize'     : 2000,
    'mergeSize'     : 10,
    'model'         : 2,
    'torus'         : None,
    'solenoid'      : None,
    'multiRun'      : False,
    'mergePattern'  : 'clas_%.6d.evio.%.5d-%.5d.hipo',
    'singlePattern' : 'clas_%.6d.evio.%.5d.hipo',
    'fileRegex'     : RunFileUtil.getFileRegex(),
    'submit'        : False
}

class ChefConfig:

  def __init__(self,args):

    self._workflow=None

    self.cfg=copy.deepcopy(CFG)

    self._setCli()

    self.args = self.cli.parse_args(args)

    if self.args.defaults:
      sys.exit(str(self))

    if self.args.config is not None:
      self._readConfigFile(self.args.config)

    self._parseCliArgs()

    self._checkConfig()

    if self.args.show:
      sys.exit(str(self))

  def get(self,key):
    return self.cfg[key]

  def getWorkflow(self):
    if self._workflow is None:
      name='%s-%s-%s'%(self.cfg['runGroup'],self.cfg['task'],self.cfg['tag'])
      name+='_R%dx%d'%(self.cfg['runs'][0],len(self.cfg['runs']))
      if self.cfg['model']!=2:
        name+='_x%d'%(self.cfg['phaseSize'])
      if self.cfg['model']==0:
        self._workflow = CLAS12Workflows.ThreePhaseDecoding(name,self.cfg)
      elif self.cfg['model']==1:
        self._workflow = CLAS12Workflows.RollingDecoding(name,self.cfg)
      elif self.cfg['model']==2:
        self._workflow = CLAS12Workflows.SinglesOnlyDecoding(name,self.cfg)
      elif cfg['model']==3:
        self._workflow = CLAS12Workflows.DecodingReconTest(name,self.cfg)
      else:
        sys.exit('This should never happen #1.')
    if self._workflow.getFileCount()<1:
      sys.exit('FATAL ERROR:  found no applicable input files.  Check "inputs" and "run".')
    return self._workflow

  def _setCli(self):

    self.cli=argparse.ArgumentParser(description='Generate a CLAS12 SWIF workflow.',
        epilog='* = required option, from command-line or config file')

    self.cli.add_argument('--runGroup',metavar='NAME',help='* run group name', type=str, choices=RUNGROUPS, default=None)
    self.cli.add_argument('--tag',     metavar='NAME',help='* workflow name suffix/tag, e.g. v0, automatically prefixed with runGroup and task to define workflow name',  type=str, default=None)
    self.cli.add_argument('--task',    metavar='NAME',help='* task name', type=str, choices=TASKS, default=None)
    self.cli.add_argument('--model', help='* workflow model (0=ThreePhase, 1=Rolling, 2=SinglesOnly)', type=int, choices=MODELS,default=None)

    self.cli.add_argument('--inputs', metavar='PATH',help='* name of file containing a list of input files, or a directory to be searched recursively for input files, or a shell glob of either.  This option is repeatable.',action='append',type=str,default=[])
    self.cli.add_argument('--runs',   metavar='RUN/PATH',help='* run numbers (e.g. 4013 or 4013,4015 or 3980,4000-4999), or a file containing a list of run numbers.  This option is repeatable and not allowed in config file.', action='append', default=[], type=str)

    self.cli.add_argument('--outDir', metavar='PATH',help='* final data location', type=str,default=None)
    self.cli.add_argument('--workDir',metavar='PATH',help='temporary data location (for merging workflows only)', type=str,default=None)

    self.cli.add_argument('--coatjava',metavar='PATH',help='coatjava install location', type=str,default=None)

    self.cli.add_argument('--phaseSize', metavar='#',help='number of files per phase', type=int, default=None)
    self.cli.add_argument('--mergeSize', metavar='#',help='number of files per merge', type=int, default=None)

    self.cli.add_argument('--torus',    metavar='#.#',help='override RCDB torus scale',   type=float, default=None)
    self.cli.add_argument('--solenoid', metavar='#.#',help='override RCDB solenoid scale',type=float, default=None)

    self.cli.add_argument('--fileRegex',metavar='REGEX',help='input filename format (for matching run and file numbers)', type=str, default=None)

    self.cli.add_argument('--multiRun', help='allow multiple runs per phase (non-merging workflow only)', action='store_true', default=None)

    self.cli.add_argument('--config',metavar='PATH',help='load config file (contents superceded by command line arguments)', type=str,default=None)
    self.cli.add_argument('--defaults',help='print default config and exit', action='store_true', default=False)
    self.cli.add_argument('--show',    help='print config and exit', action='store_true', default=False)

    #  self.cli.add_argument('--submit', help='submit and run jobs immediately', action='store_true', default=False)
    #  self.cli.add_argument('--track',   metavar='NAME',help='scicomp batch track name',   type=str, default=None)

    self.cli.add_argument('--version',action='version',version='0.1')

  def _readConfigFile(self,filename):

    if not os.access(filename,os.R_OK):
      sys.exit('Config file is not readable:  '+filename)

    try:
      cfg = json.load(open(filename,'r'))
    except:
      print traceback.format_exc()
      sys.exit('FATAL ERROR: Config file '+filename+' has invalid JSON format.')

    for key,val in cfg.iteritems():
      if key not in self.cfg:
        sys.exit('FATAL ERROR:  Config file contains invalid key:  '+key)
      if key == 'model' and val not in MODELS:
        sys.exit('Config file contans invalid model:  '+val)
      if key == 'task' and val not in TASKS:
        sys.exit('Config file contains invalid task:  '+val)
      if key == 'runGroup' and val not in RUNGROUPS:
        sys.exit('Config file contains invalid runGroup:  '+val)
      if key == 'track' and val not in TRACKS:
        sys.exit('Config file contains invalid track:  '+val)
      self.cfg[key]=val

  def _parseCliArgs(self):
    for key,val in vars(self.args).iteritems():
      if key in self.cfg:
        if val is None:
          continue
        if type(val) is list and len(val)==0:
          continue
        self.cfg[key]=val

  def _checkConfig(self):

    if self.cfg['runGroup'] is None:
      self.cli.error('"runGroup" must be defined.')
    if self.cfg['runGroup'] not in RUNGROUPS:
      self.cli.error('Invalid "runGroup":  '+str(self.cfg['runGroup'])+' is not in '+str(RUNGROUPS))

    if self.cfg['tag'] is None:
      self.cli.error('"tag" must be specified.')

    if len(self.args.runs)==0:
      self.cli.error('"runs" must be specified via --runs.')

    if len(self.cfg['inputs'])==0:
      self.cli.error('"inputs" must be specified.')

    if self.cfg['outDir'] is None:
      self.cli.error('"outDir" must be specified.')

    # non-merging workflows:
    if self.cfg['model']==2:

      if self.cfg['workDir'] is not None:
        print 'WARNING:  ignoring "workDir" for non-merging workflow.'
        self.cfg['workDir']=None

      if self.cfg['fileRegex'] != RunFileUtil.getFileRegex():
        RunFileUtil.setFileRegex(self.cfg['fileRegex'])

    # merging workflow have some additional constraints:
    else:

      if self.cfg['workDir'] is None:
        self.cli.error('"workDir" must be defined for merging workflows.')

      if self.cfg['phaseSize']%self.cfg['mergeSize']!=0:
        self.cli.error('"phaseSize" must be a multiple of "mergeSize".')

      if self.cfg['fileRegex'] != RunFileUtil.getFileRegex():
        self.cli.error('Non-default "fileRegex" is not allowed in merging workflows.')

      if self.cfg['multiRun']:
        self.cli.error('"multiRun" is not allowed in merging workflows.')

    # parse run list:
    self.cfg['runs'] = ChefUtil.getRunList(self.args.runs)
    if self.cfg['runs'] is None or len(self.cfg['runs'])==0:
      self.cli.error('\nFound no runs.  Check --inputs and --runs.')


  def __str__(self):
    return json.dumps(self.cfg,indent=2,separators=(',',': '),sort_keys=True)

  def __dict__(self):
    return self.cfg

if __name__ == '__main__':
  cc=ChefConfig(sys.argv[1:])
  print str(cc)

