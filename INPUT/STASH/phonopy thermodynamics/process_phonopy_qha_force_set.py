import os
from subprocess import call
import glob
import numpy as np
import run_module as rmd


if __name__ == '__main__':
    """

    Use phonopy to analyze each displacement run of each volume run.

    Not a VASP run script that requires a job submission. You can directly use
    it as

        INPUT/process_phonopy_qha_force_set.py INPUT/run_phonopy_qha_force_set.yaml

    to read a specs file at INPUT/run_phonopy_qha_force_set.yaml, which is the
    file you would use to actually run the routine script
    run_phonopy_qha_force_set-para.py before this.

    """

    run_specs, filename = rmd.get_run_specs_and_filename()
    rmd.chdir(rmd.get_run_dir(run_specs))

    phonopy_dim = ' '.join(map(str, run_specs['phonopy']['dim']))
    phonopy_mp = ' '.join(map(str, run_specs['phonopy']['mp']))
    phonopy_tmax = str(run_specs['phonopy']['tmax'])
    phonopy_tstep = str(run_specs['phonopy']['tstep'])
    fitting_results = rmd.fileload('../run_volume/fitting_results.json')[-1]
    volume = np.round(np.array(fitting_results['volume']), 2)

    for V in volume:
        rmd.chdir(str(V))
        disp_dirs = sorted(glob.glob('disp-*'))
        disp_vasprun_xml = ' '.join([i + '/vasprun.xml' for i in disp_dirs])
        call('phonopy -f ' + disp_vasprun_xml + ' > /dev/null', shell=True)
        call('phonopy --mp="' + phonopy_mp + '" -tsp --dim="' + phonopy_dim + '" --tmax=' + phonopy_tmax + ' --tstep=' + phonopy_tstep + ' > /dev/null', shell=True)
        os.chdir('..')

    # post processing
    fitting_results = rmd.fileload('../run_volume/fitting_results.json')[-1]
    e_v_dat = np.column_stack((fitting_results['volume'], fitting_results['energy']))
    np.savetxt('../e-v.dat', e_v_dat, '%15.6f', header='volume energy')
    thermal_properties = ' '.join([str(i) + '/thermal_properties.yaml' for i in volume])
    call('phonopy-qha ../e-v.dat ' + thermal_properties + ' --tmax=' + phonopy_tmax + ' > /dev/null', shell=True)
