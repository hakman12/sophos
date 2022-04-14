#############################################################
# Author: Hakob Manukyan
#
# This script is for processing pipline configuration file 
# and create or update Sophos Factory pipeline, create a 
# new revision and execute it  
#
#############################################################

import os
import json
import requests
import re
import logging


#Environement variables names
LOG_LEVEL = "LOG_LEVEL"
PIPELINE_CONFIG_FILE_NAME = "PIPELINE_CONFIG_FILE_NAME"
PIPELINE_NAME = "PIPELINE_NAME"
PIPELINE_COMMENT = "PIPELINE_COMMENT"
PROJECT_ID = "PROJECT_ID"
AUTH_TOKEN_NAME = "AUTH_TOKEN_NAME"
TASK_OPERATION_DIR_PATH = "TASK_OPERATION_DIR_PATH"

#Supported values for LOG_LEVEL (DEBUG,INFO, WARNING)
FORMAT = '%(levelname)s: %(message)s'
logging.basicConfig(format=FORMAT)

_log_level = os.environ.get(LOG_LEVEL, "WARNING")
_logger = logging.getLogger("pipeline")
_logger.setLevel(getattr(logging, _log_level))

print(f"Log level set to {_log_level}")

##############################################################################
# description: This function intitiate gloabl varaibles with environement 
#              varailable values and  
#
# name: init_params
# params: N/A
##############################################################################
def init_params ():

    global _cfg_name
    global _cfg_file
    global _pipeline
    global _project_id
    global _rev_comment
    global _pipelinename
    global _access_token
    global _base_url
    global _task_oper_dir

    #Pipeline file name
    if PIPELINE_CONFIG_FILE_NAME not in os.environ.keys():
        _logger.error("There is no pipeline config name(path) defined")
        exit (1)        

    
    _cfg_name = os.environ[PIPELINE_CONFIG_FILE_NAME]
    _logger.debug(f"_cfg_name={_cfg_name}")

    #Open pipeline config file 
    _cfg_file = open(_cfg_name, 'r')
    if not _cfg_file:
        _logger.error("There is no pipeline config file");
        exit (1)
    
    #Load the file content as  
    _pipeline = json.load(_cfg_file)
    _logger.info(f"Pipeline configuration\n{_pipeline}")

    #Sophos Factory project ID
    if PROJECT_ID not in os.environ.keys():
        _logger.error("There is no project_id defined");
        exit (1)
        
    _project_id = os.environ[PROJECT_ID]
    _logger.debug(f"_project_id={_project_id}")

    #Pipeline Name
    if PIPELINE_NAME not in os.environ.keys():
        _logger.error("There is no pipleine name defined");
        exit (1)
        
    _pipelinename = os.environ[PIPELINE_NAME]
    _logger.debug(f"_pipelinename={_pipelinename}")
    
    
    #Sophos Factory API access token
    if AUTH_TOKEN_NAME not in os.environ.keys():
        _logger.error("There is no access_token defined");
        exit (1)
        
    #It is not secured to print the token even for debugging
    _access_token = os.environ[AUTH_TOKEN_NAME]
    
    
    #Sophos Factory API base URL for pipelines(API version V_1)
    _base_url = f'https://api.refactr.it/v1/projects/{_project_id}/pipelines'
    _logger.debug(f"base_url={_base_url}")
    
    #Pipeline revision comment, default valu is "New Commit"
    _rev_comment = os.environ.get(PIPELINE_COMMENT, "New Commit")
    _logger.debug(f"_rev_comment={_rev_comment}")
    
    #Task operation directory path, default is the current directory
    _task_oper_dir = os.environ.get(TASK_OPERATION_DIR_PATH, ".")
    _logger.debug(f"_task_oper_dir={_task_oper_dir}")


##############################################################################
# description: This function generates 'env' field of step based on 
#              pipeline task 'prop'
# 
# name: generate_steps
# param: props,
# param type: "props": {
#                        "num1": 3,
#                        "num2": 6
#                      }
#
# return: returns genrated string dictionary
############################################################################## 
def generate_steps (props):
    valuestr = ""
    
    first = True;
    for key in props:
        
        if first:
            first = False
        else:
           valuestr += ", " 
        
        valuestr += "{"        
        valuestr += "'name' : "
        valuestr += "'" + key + "',"
        valuestr += "'value': "
        

# regex used for remove doulbe brackets from the value {{ tasks.three.result }}
        replace = re.search("[^{\{]+(?=}\})", f"{props[key]}")
        if replace:
            res = replace.group(0).split('.')

# converts {{ tasks.three.result }} to Sophos API format 'steps.three.result.stdout'
            if len(res) == 3 and res[0].lower().strip() == "tasks" and res[2].lower().strip() == "result":
                valuestr += f"steps.{res[1]}.result.stdout"
        else:
            valuestr += "'" + str(props[key]) + "'";
        valuestr += "}"
        
    return valuestr

##############################################################################
# description: This function returns piplenid of exiisnt piplein or creates 
#              new pipeline and return pipeline_id 
# 
# name: get_pipeline
# param: name - pipeline name
# param type: str
#
# return: pipeline_id
##############################################################################     
def get_pipeline (name):
    pipeline_id = "";
    
    search_url = f'{_base_url}?search={name}'; 
    headers = {'accept' : 'application/json', 'Authorization' : f'Bearer {_access_token}'}

# Try to get pipeline by name if it exists
    resp = requests.get(search_url, headers=headers);
    if not resp.ok:
        _logger.error(f" {resp.status_code} - {resp.reason}, It was impossible to compete the request")
        exit(1)

    
    allpipelines = resp.json().get('pipelines')
    

    print(resp.json())

    if not allpipelines:
        #There is no such pipeline and needs to be created
        print("No such pipeline, needs to be created")
        
        data = {'name': f'{name}'}
        print(data["name"])
        headers = {'accept' : 'application/json', 'Content-Type' : 'application/json', 'Authorization' : f'Bearer {_access_token}'}
        
        #Try to create new pipeline 
        _logger.info(f"Sending request: {_base_url}")
        resp = requests.post(_base_url, json=data, headers=headers);        
        if not resp.ok:
            _logger.error(f"{resp.status_code} - {resp.reason}, It was impossible to create the pipeline {_base_url}")
            exit(1)
        
        _logger.info(f"Response: {resp.json()}")
        pipeline_id = resp.json().get('_id');
        
    else:
        #There is already such pipeline
        pipeline_id = allpipelines[0]['_id'];
        
    _logger.info(f"Pipeline_id = {pipeline_id}")

    return pipeline_id   


##############################################################################
# description: This function creates a reviison for the given platform and 
#              returns revision id
#              
# 
# name: create_reviison
# param: pipeline_id
# param type: str
#
# return: reviison_id 
##############################################################################    
def create_reviison(pipeline_id):

    steps = []

     
    #Prepare steps section of request data
    for task in _pipeline.get('tasks'):

        operation_file = open(f'{_task_oper_dir}/{task["type"]}.py')
        operation = operation_file.read()
        step = {"id": task["id"],
              "name": task["id"],
              "type": "python_script",
              "depends": task["needs"],
              
              
        }
        
        valuestr = "{|["
        
        valuestr += generate_steps(task['props'])
        valuestr += "]|}"

        step["properties"] = {
                "content": operation,
                "env": valuestr
        }
          
        steps.append(step);
          

        
    if not len(steps):
        _logger.warning("No tasks in the pipleine description")
        

    #Prepare API request data 
    data = {
      "comment": _rev_comment,
      "steps": steps,
      "variables": [
        {}
      ],
      "outputs": [
        
      ],
      "layout": {"elements": []}
    }

    url_revisions = f'{_base_url}/{pipeline_id}/revisions'

    _logger.debug(f"new revision data: {json.dumps(data)}")

    headers = {'accept' : 'application/json', 'Content-Type' : 'application/json', 'Authorization' : f'Bearer {_access_token}'}
    
    _logger.info(f"Sending request: {url_revisions}")
    #Try to create new revision for the pipeline
    resp = requests.post(url_revisions, json=data, headers=headers);    
    if not resp.ok:
        _logger.error(f"{resp.status_code} - {resp.reason}, It was impossible to compete the request")
        exit(1)
        
    _logger.info(f"Response: {resp.json()}")
    
    return resp.json().get('_id');

##############################################################################
# description: This function run the pipeline of the given revision_id 
#              and pipeline_id 
#              
#              
# 
# name: create_reviison
# param_1:      pipeline_id
# param_1:      type: str
# param_2:      revision_id
# param_2 type: str
#
# return: run_id 
##############################################################################       
def run_pipeline(pipeline_id, reviison_id):
    data = {  "variables": {},
              "suppress_vars": False,
              "suppress_events": False,
              "suppress_outputs": False
    }
    

    url_revision = f'{_base_url}/{pipeline_id}/revisions/{reviison_id}/run'

    _logger.debug(f"revisin run data: {json.dumps(data)}")
    
    headers = {'accept' : 'application/json', 'Content-Type' : 'application/json', 'Authorization' : f'Bearer {_access_token}'}
    
    _logger.info(f"Sending request: {url_revision}")
    #Try to run given revision of pipeline
    resp = requests.post(url_revision, json=data, headers=headers);
    if not resp.ok:
        print(f"Error: {resp.status_code} - {resp.reason}, It was impossible to compete the request")
        exit(1)
    _logger.info(f"Response: {resp.json()}")
    
    _logger.info("Pipeline was started")

    
#init params
init_params()
_logger.info(f"project_id = {_project_id}")


#get or create pipeline by name  
_pipeline_id = get_pipeline(_pipelinename)

#create new revision for the pipeline
_revision_id = create_reviison(_pipeline_id)
_logger.info(f"_revision_id = {_revision_id}")

#run the pipeline
run_pipeline(_pipeline_id, _revision_id)

_logger.info("Successful!")




    
    