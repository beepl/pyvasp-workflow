import os
import sys
import shutil
from subprocess import call
import glob
import numpy as np
from run_module import rm_stdout, detect_is_mag, fileload, filedump, chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure, VASP
import pymatgen as mg


if __name__ == '__main__':
    filename = sys.argv[1]
    run_spec = fileload(filename)
    os.remove(filename)
    phonopy_dim = ' '.join(map(str, run_spec['phonopy']['dim']))

    enter_main_dir(run_spec)
    filedump(run_spec, filename)

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
    if detect_is_mag(properties['mag']):
        incar.update({'ISPIN': 2})
    else:
        incar.update({'ISPIN': 1})
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
            rm_stdout()
            shutil.move('../' + disp_p, 'POSCAR')
            incar.write_file('INCAR')
            kpoints.write_file('KPOINTS')
            write_potcar(run_spec)
            job = str(V) + '-' + disp_d
            shutil.copy('../../../../INPUT/deploy.job', job)
            call('sed -i "/python/c time ' + VASP + ' > stdout" ' + job, shell=True)
            call('qsub ' + job, shell=True)
            os.chdir('..')
        os.chdir('..')
