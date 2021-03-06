#!/usr/bin/env python
import sys,os,logging
from ChefConfig import ChefConfig

#logging.basicConfig(level=logging.INFO,format='%(levelname)-9s[%(name)-14s %(lineno).3d] %(message)s')
logging.basicConfig(level=logging.INFO,format='%(levelname)-9s[%(name)-14s] %(message)s')
logger=logging.getLogger(__name__)

print('')
cc=ChefConfig(sys.argv[1:])
workflow=cc.getWorkflow()

logger.info('Generating workflow ...')
workflow.generate()

logger.info('Created workflow with %d jobs based on %d runs with %d total input files.'%\
    (len(workflow.jobs),len(workflow.getRunList(1)),workflow.getFileCount()))

if os.path.exists(workflow.name+'.json'):
  logger.critical('File already exists:  '+workflow.name+'.json')
  sys.exit()

logger.info('Writing workflow to ./'+workflow.name+'.json ...')
with open(workflow.name+'.json','w') as out:
  out.write(workflow.getJson())

if cc.get('submit'):
  logger.info('Submitting %s.json with %d jobs ...'%(workflow.name,len(workflow.jobs)))
  workflow.submitJson()

