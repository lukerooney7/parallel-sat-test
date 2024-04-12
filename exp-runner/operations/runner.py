import os
import tempfile
import json
import time
from collections import defaultdict

from unified_planning.shortcuts import *
from unified_planning.io import PDDLReader
from unified_planning.plans import SequentialPlan

from omtplan.shortcuts import *

from .utilities import getkeyvalue

def solve(args):
    
    
    with tempfile.TemporaryDirectory(dir=args.run_dir) as tmpdirname:
        planner_cfg       = json.load(open(args.planner_cfg_file))
        planner_tag       = getkeyvalue(planner_cfg, 'planner-tag')
        up_planner_name   = getkeyvalue(planner_cfg, 'up-planner-name')
        up_planner_params = getkeyvalue(planner_cfg, 'planner-params')
        
        assert up_planner_name is not None, "up-planner-name is not defined in the planner configuration file."
        assert up_planner_params is not None, "planner-param is not defined in the planner configuration file."
        assert planner_tag is not None, "planner-tag is not defined in the planner configuration file."

        start_time = time.time()
        task = PDDLReader().parse_problem(args.domain, args.problem)
        end_time = time.time()
        pddl_parse_time = end_time - start_time

        start_time = time.time()
        with OneshotPlanner(name=up_planner_name,  params=up_planner_params) as planner:
            result = planner.solve(task)
            seedplan = result.plan if result.status in unified_planning.engines.results.POSITIVE_OUTCOMES else SequentialPlan([], task.environment)
        end_time = time.time()
        planning_time = end_time - start_time

        # Now we need to construct the task result.
        dumpresult = defaultdict(dict)
        dumpresult['task-info'] = defaultdict(dict)
        dumpresult['task-info']['domain'] = args.domainname
        dumpresult['task-info']['instance'] = args.instanceno
        dumpresult['task-info']['ipc-year'] = args.ipc_year

        dumpresult['planner-info'] = defaultdict(dict)  
        dumpresult['planner-info']['planner-tag'] = planner_tag
        dumpresult['planner-info']['planner-name'] = up_planner_name
        dumpresult['planner-info']['planner-params'] = up_planner_params

        dumpresult['task-result'] = defaultdict(dict)
        dumpresult['task-result']['timings'] = defaultdict(dict)
        dumpresult['task-result']['timings']['pddl-parse-time'] = pddl_parse_time
        dumpresult['task-result']['timings']['planning-time'] = planning_time

        dumpresult['task-result']['summary'] = defaultdict(dict)
        dumpresult['task-result']['summary']['status'] = result.status.name
        dumpresult['task-result']['summary']['log_messages'] = [] if result.log_messages is None else result.log_messages

        dumpresult['task-result']['plan'] = [action for action in str(seedplan).split()[1:]]
        
        # Dump this to the output directory.
        dumpfile = os.path.join(args.results_dump_dir, f"{planner_tag}-{args.domainname}-{args.instanceno}-{args.ipc_year}.json")
        # make sure that the directory exists
        os.makedirs(os.path.dirname(dumpfile), exist_ok=True)
        with open(dumpfile, 'w') as dumpfilehandle:
            json.dump(dumpresult, dumpfilehandle, indent=4)