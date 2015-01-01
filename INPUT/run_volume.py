import os
import sys
import shutil
import json
import yaml
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.style.use('ggplot')
import pymatgen as mg
import pydass_vasp
from run_module import chdir, enter_main_dir, run_vasp, read_incar_kpoints, write_potcar, generate_structure


def volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag)):
    """
    loop over a set of volumes
    """
    for i, V in enumerate(volume):
        volume_str = '{:.2f}'.format(V)
        chdir(volume_str)
        incar.write_file('INCAR')
        kpoints.write_file('KPOINTS')
        structure.scale_lattice(V)
        structure.to(filename='POSCAR')
        write_potcar(run_spec)
        run_vasp()
        # energy[i] = mg.io.vaspio.Vasprun('vasprun.xml', parse_dos=False, parse_eigen=False).final_energy
        oszicar = mg.io.vaspio.Oszicar('OSZICAR')
        energy[i] = oszicar.final_energy
        mag[i] = oszicar.ionic_steps[-1]['mag']
        os.chdir('..')

    fitting_params = pydass_vasp.fitting.eos_fit(volume, energy, save_figs=True)['parameters']
    with open('fitting_params.json', 'w') as f:
        json.dump(fitting_params, f, indent=4)

    return fitting_params


def detect_is_mag(mag):
    if isinstance(mag, np.ndarray):
        is_mag = (mag > 0.01).all()
    elif isinstance(mag, float):
        is_mag = mag > 0.01
    return is_mag


if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename) as f:
        run_spec = yaml.load(f)

    enter_main_dir(run_spec)
    (incar, kpoints) = read_incar_kpoints(run_spec)
    structure = generate_structure(run_spec)
    properties = {}

    # first round
    chdir('volume_run1')
    volume_params = run_spec['volume']
    volume = np.linspace(volume_params['begin'], volume_params['end'], volume_params['sample_point_num'])
    energy = np.zeros(len(volume))
    mag = np.zeros(len(volume))
    fitting_params = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag))
    os.chdir('..')
    is_mag = detect_is_mag(mag)
    if not is_mag:
        incar.update({'ISIF': 1})

    # second round
    V0 = fitting_params['V0']
    V0_ralative_pos = (V0 - volume_params['begin']) / (volume_params['end'] - volume_params['begin'])
    is_V0_within_valley = bool(V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6)

    if not is_V0_within_valley:
        chdir('volume_run2')
        V_begin = V0 * 9./10
        V_end = V0 * 11./10
        volume = np.linspace(V_begin, V_end, 5)
        energy = np.zeros(len(volume))
        mag = np.zeros(len(volume))
        fitting_params = volume_loop_fitting(run_spec, (incar, kpoints, structure), (volume, energy, mag))
        os.chdir('..')
        is_mag = detect_is_mag(mag)

        V0 = fitting_params['V0']
        V0_ralative_pos = (V0 - V_begin) / (V_end - V_begin)
        is_V0_within_valley = bool(V0_ralative_pos > 0.4 and V0_ralative_pos < 0.6)

    # equi_relax
    chdir('equi_relax')
    incar.write_file('INCAR')
    kpoints.write_file('KPOINTS')
    structure.scale_lattice(V0)
    structure.to(filename='POSCAR')
    write_potcar(run_spec)
    run_vasp()
    oszicar = mg.io.vaspio.Oszicar('OSZICAR')
    energy = oszicar.final_energy
    mag = oszicar.ionic_steps[-1]['mag']
    os.chdir('..')
    is_mag = detect_is_mag(mag)

    properties.update({'is_V0_within_valley': is_V0_within_valley})
    properties.update(fitting_params)
    properties.update({'E0': energy, 'is_mag': is_mag})
    if is_mag:
        properties.update({'mag': mag})

    with open('properties.json', 'w') as f:
        json.dump(properties, f, indent=4)
