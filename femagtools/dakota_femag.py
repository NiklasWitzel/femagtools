"""
  Dakota Interface
 called by dakota with 2 args: in out
"""
import sys
import pathlib
import logging
import femagtools.grid
import model
import importlib
import os


# read params in
#           3 variables
#                3.000000000000000e-03 stator.statorRotor3.slot_width
#                8.000000000000000e-01 magnet.magnetSector.magn_width_pct
#                2.100000000000000e-02 magnet.magnetSector.magn_shape
#           3 functions
#                1 ASV_1:machine.torque
#                1 ASV_2:torque[-1].ripple
#                1 ASV_3:torque[0].ripple
#            3 derivative_variables
#                1 DVV_1:stator.statorRotor3.slot_width
#                2 DVV_2:magnet.magnetSector.magn_width_pct
#                3 DVV_3:magnet.magnetSector.magn_shape
#           0 analysis_components
#            1 eval_id
#
#
def read_paramsin(p):
    paramsin = p.read_text().split('\n')

    b = 0
    d = []
    while b < len(paramsin):
        numin = int(paramsin[b].split()[0])
        numout = int(paramsin[b+numin+1].split()[0])
        columns = []
        row = []
        for l in paramsin[1+b:1+numin+b]:
            v, n = [x.strip() for x in l.split()]
            columns.append(n)
            row.append(float(v))
        d.append(row)
        if l:
            resvars = [l.split(':')[-1]
                       for l in paramsin[b+numin+2:b+numin+numout+2]]
        b = b + 2 + numin + numout
        i = b
        for l in paramsin[i:]:
            if l and l.split()[-1] == 'variables':
                break
            b = b+1

    return {
        "objective_vars": [{'name': v} for v in resvars],
        "population_size": 20,
        "decision_vars": {
            'list': d,
            'columns': columns}
    }


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')

    parvardef = read_paramsin(pathlib.Path(sys.argv[1]))

    magnetizingCurve = "."

    workdir = pathlib.Path.home() / 'dakota'
    workdir.mkdir(parents=True, exist_ok=True)

    parvar = femagtools.parstudy.List(workdir,
                                      magnetizingCurves=magnetizingCurve,
                                      magnets=model.magnetMat)

    config = dict(
        module=os.environ.get('FEMAGTOOLS_ENGINE', 'femagtools.multiproc'))
    for envname in ('ENGINE_NUM_THREADS', 'ENGINE_PORT', 'ENGINE_DISPATCHER',
                    'ENGINE_PROCESS_COUNT', 'ENGINE_CMD'):
        if os.environ.get(envname):
            k = '_'.join(envname.lower().split('_')[1:])
            config[k] = os.environ.get(envname)
    cfg = pathlib.Path('engine.conf')
    if cfg.exists():
        for l in cfg.read_text().split('\n'):
            k, n = l.split('=')
            config[k.strip()] = n.strip()

    module = importlib.import_module(config['module'])
    config.pop('module')
    engine = module.Engine(**config)
    results = parvar(parvardef, model.machine, model.simulation, engine)

    # save results:
    resvars = [o['name'] for o in parvardef['objective_vars']]
    with open(sys.argv[2], 'w') as fp:
        for r in zip(*(results['f'])):
            fp.write('#\n')
            for c, v in zip(r, resvars):
                fp.write(f' {c} {v}\n')