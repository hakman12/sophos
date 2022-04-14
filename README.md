## **Workflow Engine - Sophos Factory pipeline generator**

This engine creates a pipeline based on a configuration file that has json format. The engine is written in python and all the logic is parser.py. It reads pipeline configuration file and uses [Sophos Factory API v1](https://api.refactr.it/v1/) to create/update the pipeline with new revision. After successful creation of the revision, it calls API to run the revision of the pipeline.

The tasks folder in repo includes python files for each type of task. For example, if the type of task is “add”, tasks folder should include file with the name "add.py" so the parser can inject the python content into the content section of Sophos Factory Pytho script step module. This architecture allows us to add **new task types** easily. Currently, the pipeline supports 3 types of tasks:

* add
* subtract
* print

---

## Run command from command line

python parser.py

---

## Pipeline configuration pipeline.json file format 

pipeline.json

```javascript
{
"tasks": [{
"id": "one",
"type": "print",
"needs": [],
"props": {
"message": "Hello!"
}
},{
"id": "two",
"type": "subtract",
"needs": ["three"],
"props": {
"num1": 21,
"num2": "{{ tasks.three.result }}"
}
},{
"id": "three",
"type": "add",
"needs": ["one"],
"props": {
"num1": 3,
"num2": 6
}
}]
}
```

_Note: The format was provided in the_ [_Workflow Engine challenge_](https://github.com/sophos-factory/homework/blob/master/challenges/workflow-engine.md)

`id` is a unique identifier for each task. It will be converted to **step module id**

`type` defines the action performed by the task. For the type it should be added **“type\_value.py"** file into the tasks folder. 

`needs` specifies task dependencies. It will be added into the “**depends”** field.

`props` are task type-specific input properties. Based on ‘props’ will be generated. env field

```javascript
"env": "{|[{'name' : 'num1','value': '21'},
{'name' : 'num2','value': steps.three.result.stdout}
]|}"
```

The `{{ tasks.three.result }}` value will be converted to the expression style of the step module `steps.three.result.stdout`. 

---

## Environment Variables

parser.py supports the following environment variables

* LOG\_LEVEL - logging level
* Default value - WARNING
* Supported values - (WARNING, INFO, DEBUG)
* Optional
* PIPELINE\_CONFIG\_FILE\_NAME - pipeline config file name
* PIPELINE\_NAME - pipeline name that will be created or updated
* Required
* PIPELINE\_COMMENT - revision comment test
* Required
* PROJECT\_ID  - Sophos Factory project ID
* Required
* AUTH\_TOKEN\_NAME - Sophos Factory API token
* Required
* TASK\_OPERATION\_DIR\_PATH - logging level
* Default value - current directory of parser.py
* Required
 

---

## Sophos Factory API calls to create and run the pipeline

```javascript
Search the pipelein
https:/by name/api.refactr.it/v1/projects/{project_id}/pipelines?search=pieline_name

Create pipeline if it does not exist
https://api.refactr.it/v1/projects/{project_id}/pipelines

Create revision for the pipeline
https://api.refactr.it/v1/projects/{project_id}/pipelines/{pipeline_id}/revisions

Run the revision of the pipeline https://api.refactr.it/v1/projects/{project_id}/pipelines/{pipeline_id}/revisions/{revision_id}/run
```

---

## Sophos Factory pipeline description

The pipeline **generator** was created by me  with the following pipeline variables:

```javascript
"variables": [
{
"type": "SecureString",
"name": "AUTH_TOKEN_NAME",
"key": "AUTH_TOKEN_NAME",
"value": "api_token",
"required": false,
"visible": true,
"default": false
},
{
"type": "String",
"name": "PIPELINE_CFG_REPO",
"key": "PIPELINE_CFG_REPO",
"value": "https://github.com/hakman12/sophos_tasks.git",
"required": true,
"visible": true,
"default": true
},
{
"type": "String",
"name": "PIPELINE_CFG_REPO_BRANCH",
"key": "PIPELINE_CFG_REPO_BRANCH",
"value": "sit",
"required": true,
"visible": true,
"default": true
},
{
"type": "String",
"name": "PIPELINE_ENV",
"key": "PIPELINE_ENV",
"value": "sit",
"required": false,
"visible": true,
"default": true
},
{
"type": "String",
"name": "PIPELINE_BASE_NAME",
"key": "PIPELINE_BASE_NAME",
"value": "tasks",
"required": false,
"visible": true,
"default": true
},
{
"type": "String",
"name": "PROJECT_ID",
"key": "PROJECT_ID",
"value": "624e09ee92b7582a9f451436",
"required": false,
"visible": true,
"default": true
},
{
"type": "String",
"name": "LOG_LEVEL",
"key": "LOG_LEVEL",
"value": "INFO",
"required": false,
"visible": true,
"default": true
}
]
```

It includes the following step modules:

*  2 git clone step module (1 repo is for parser and another one is for pipeline config file). 
* python install
* shell script
* set variable

All necessary pipeline variables(i.e git repos, branches, environment sit, guat, prod) are set to be able to generate pipelines dynamically. The pipelin name will be constructed as **pipelinename\_envname**, i.e tasks-sit.

as a result of running the generator pipeline tasks-sit was created. It includes 3 python step module:

```javascript
{
"_id": "62582f9a2e572e96d9f768f2",
"variables": [],
"steps": [
{
"id": "one",
"name": "one",
"type": "python_script",
"depends": [],
"properties": {
"content": "#############################################################\n# Author: Hakob Manukyan\n#\n# This script for execute a task 'print'\n#\n#############################################################\n\nimport os\nimport ast\n\nmessage = os.environ['message'].strip('\"')\n\nprint(message);",
"env": "{|[{'name' : 'message','value': 'Hello!'}]|}"
}
},
{
"id": "two",
"name": "two",
"type": "python_script",
"depends": [
"three"
],
"properties": {
"content": "#############################################################\n# Author: Hakob Manukyan\n#\n# This script for execute a task 'subtract'\n#\n#############################################################\n\nimport os\nimport ast\n\nimport os\nimport ast\n\nnum1 = int(os.environ['num1'])\nnum2 = int(os.environ['num2'])\n\nprint(num1 - num2);",
"env": "{|[{'name' : 'num1','value': '21'}, {'name' : 'num2','value': steps.three.result.stdout}]|}"
}
},
{
"id": "three",
"name": "three",
"type": "python_script",
"depends": [
"one"
],
"properties": {
"content": "#############################################################\n# Author: Hakob Manukyan\n#\n# This script for execute a task 'add'\n#\n#############################################################\n\nimport os\nimport ast\n\nimport os\nimport ast\n\nnum1 = int(os.environ['num1'])\nnum2 = int(os.environ['num2'])\n\nprint(num1 + num2);",
"env": "{|[{'name' : 'num1','value': '3'}, {'name' : 'num2','value': '6'}]|}"
}
}
],
"organization_id": "62449c960578758705c15e7c",
"project_id": "624e09ee92b7582a9f451436",
"pipeline_id": "625828462d3d5a4ce4df5263",
"user_id": "62524b5353fa4a3cf0b74942",
"created": "2022-04-14T14:28:42.464Z",
"comment": "New Commit",
"outputs": [],
"layout": {
"elements": []
},
"revision": 2
}
```