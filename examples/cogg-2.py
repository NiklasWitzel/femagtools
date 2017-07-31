import femagtools
import os
import logging

mcvData = dict(curve=[dict(
    bi=[0.0, 0.09, 0.179, 0.267, 0.358,
        0.45, 0.543, 0.6334, 0.727,
        0.819, 0.9142, 1.0142, 1.102,
        1.196, 1.314, 1.3845, 1.433,
        1.576, 1.677, 1.745, 1.787,
        1.81, 1.825, 1.836],

    hi=[0.0, 22.16, 31.07, 37.25, 43.174,
        49.54, 56.96, 66.11, 78.291,
        95, 120.64, 164.6, 259.36,
        565.86, 1650.26, 3631.12, 5000, 10000,
        15000, 20000, 25000, 30000, 35000, 40000]
    )],
    name='m270-35a',
    desc=u"Demo Steel",
    ch=4.0,
    cw_freq=2.0,
    cw=1.68)

mcv = femagtools.mcv.MagnetizingCurve(mcvData)

machine = dict(
    name="PM 225 8",
    lfe=0.1,
    poles=8,
    outer_diam=0.225,
    bore_diam=0.1615,
    inner_diam=0.120,
    airgap=0.0015,
     
    stator=dict(
        num_slots=48,
        mcvkey_yoke="m270-35a",
        rlength=1.0,
        statorRotor3=dict(
            slot_height=0.0197,
            slot_h1=0.001,
            slot_h2=0.001,
            slot_width=0.003,
            slot_r1=0.0,
            slot_r2=0.0,
            wedge_width1=0.0,
            wedge_width2=0.0,
            tooth_width=0.005,
            middle_line=1,
            slot_top_sh=1)
    ),
    
    magnet=dict(
        mcvkey_shaft="dummy",
        mcvkey_yoke="m270-35a",
        magnetSector=dict(
            magn_num=1,
            magn_width_pct=0.8,
            magn_height=0.005,
            magn_shape=0.0,
            bridge_height=0.0,
            magn_type=1,
            condshaft_r=0.02,
            magn_ori=2,
            magn_rfe=0.0,
            bridge_width=0.0,
            magn_len=1.0)
    ),
    
    windings=dict(
        num_phases=3,
        num_wires=4,
        coil_span=5,
	slot_indul=0,
        num_layers=2)
    )

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(message)s')

workdir = os.path.join(
    os.path.expanduser('~'), 'femag')
try:
    os.makedirs(workdir)
except OSError:
    pass

femag = femagtools.Femag(workdir, magnetizingCurves=mcv)


operatingConditions = dict(
    calculationMode="cogg_calc",
    magn_temp=60.0,
    num_move_steps=49,
    speed=50.0)

r = femag(machine,
          operatingConditions)

print("Order    T/Nm      %")
tq = r.torque_fft[-1]
for l in zip(tq['order'], tq['torque'], tq['torque_perc']):
    print('{0:<5} {1:9.2f} {2:6.1f}'.format(*l))

