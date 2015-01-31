import os
import sys
import shutil
from subprocess import call
import glob
import numpy as np
import matplotlib
matplotlib.use('Agg')
import pymatgen as mg
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    phonopy_dim = ' '.join(map(str, run_spec['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_spec['phonopy']['mp']))
    phonopy_tmax = str(run_spec['phonopy']['tmax'])
    phonopy_tstep = str(run_spec['phonopy']['tstep'])

    enter_main_dir(run_spec)
    filedump(run_spec, filename)
    rm_stdout()

    # for solution runs
    if run_spec.has_key('solution') and run_spec['solution'].has_key('ratio'):
        ratio = str(run_spec['solution']['ratio'])
        ratio_list = [float(i) for i in ratio.split('-')]
        if ratio_list[0] == 0 and ratio_list[1] == 1:
            run_spec['elem_types'] = [run_spec['elem_types'][1], run_spec['elem_types'][2]]
        elif ratio_list[0] == 1 and ratio_list[1] == 0:
            run_spec['elem_types'] = [run_spec['elem_types'][0], run_spec['elem_types'][2]]

    (incar, kpoints) = read_incar_kpoints(run_spec)
    properties = fileload('../properties.json')
    volume = np.round(np.array(properties['volume']), 2)
    poscars = properties['poscars']

    for V, poscar in zip(volume, poscars):
        chdir(str(V))
        structure = mg.Structure.from_dict(poscar)
        structure.to(filename='POSCAR')
        call('phonopy -d --dim="' + phonopy_dim + '" > /dev/null', shell=True)
        os.remove('SPOSCAR')
        disp_poscars = sorted(glob.glob('POSCAR-*'))
        disp_dirs = ['disp-' + i.split('POSCAR-')[1] for i in disp_poscars]

        for disp_d, disp_p in zip(disp_dirs, disp_poscars):
            chdir(disp_d)
            shutil.move('../' + disp_p, 'POSCAR')
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            write_potcar(run_spec)
            run_vasp()
            os.chdir('..')

        disp_vasprun_xml = ' '.join([i + '/vasprun.xml' for i in disp_dirs])
        call('phonopy -f ' + disp_vasprun_xml + ' > /dev/null', shell=True)
        call('phonopy --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep + ' > /dev/null', shell=True)
        os.chdir('..')

    # post processing
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in volume])
    call('phonopy-qha ../e-v.dat ' + thermal_properties + ' --tmax=' + phonopy_tmax, shell=True)
    gibbs = np.loadtxt('gibbs-temperature.dat')
    properties['gibbs'] = gibbs
    filedump(properties, '../properties.json')
