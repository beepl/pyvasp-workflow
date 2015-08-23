#!/bin/bash
task="$1"
if [[ -z $task ]]; then
    echo "You must provide task name at least!"
    exit 1
fi
shift 1

if [[ "$1" && "$1" != - ]]; then
    task_spec="$1"
    shift 1
else
    task_spec=${task}.yaml
fi

suffix=`date +%F-%T`
task_spec_suffixed=${task_spec##*/}
task_spec_suffixed=${task_spec_suffixed%.yaml}_${suffix}.yaml
python -c "
from os import chdir
chdir('INPUT')
from run_module import fileload, filedump, get_run_dir
chdir('..')
run_spec = fileload('${task_spec}')
filedump(run_spec, '${task_spec_suffixed}')
"
python INPUT/${task}.py --remove_file $task_spec_suffixed --remove_file
