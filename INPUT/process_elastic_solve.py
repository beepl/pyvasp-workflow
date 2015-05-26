import os
import sys
import shutil
import numpy as np
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure, get_test_type_strain_delta_list, solve
import pymatgen as mg
import pydass_vasp

if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    cryst_sys = run_spec['poscar']['cryst_sys']

    enter_main_dir(run_spec)
    properties = fileload('../properties.json')
    V0 = properties['V0']

    test_type_list, strain_list, delta_list = get_test_type_strain_delta_list(cryst_sys)
    fitting_results_summary = fileload('fitting_results.json')
    fitting_results_summary['c11+2c12'] = {}
    fitting_results_summary['c11+2c12']['params'] = []
    fitting_results_summary['c11+2c12']['params'].append(properties['B0'] * V0 / 160.2 * 9/2.)

    combined_econst_array = [fitting_results_summary[test_type]['params'][0] for test_type in test_type_list]
    combined_econst_array = np.array(combined_econst_array) * 160.2 / V0
    solved = solve(cryst_sys, combined_econst_array)
    filedump(solved, 'elastic.json')

    properties['elastic'] = solved
    filedump(properties, '../properties.json')
