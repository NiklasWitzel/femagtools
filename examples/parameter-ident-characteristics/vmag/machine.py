import logging
import femagtools
import pathlib

# air: spmaweight=1.12, thcond=0.026, thcap=1007
# insulation: spmaweight=1.34, thcond=0.31, thcap=1100

magnetMat = [
{
    "name": "N36Z",
    "remanenc": 1.2,
    "relperm": 1.03,
    "spmaweight": 7.55,
    "temcoefbr": -0.0015,
    "temcoefhc": -0.007,
    "magncond": 625e3,
    "thcond": 8,
    "thcap": 440
}
]
condMat = [
    {'name': 'Cu',
     "spmaweight": 8.96,
     "elconduct": 56e6,
     "tempcoef": 3.9e-3,
     "thcond": 30,
     "thcap": 480 }
    ]

laminations = [
    {"name": "M19-29G", "ctype": 1, "rho": 7.872,
     "thcond": 24, "thcap": 480,
     "curve": [{"hi": [25.46, 47.74, 63.66,
                       159.15, 477.46, 795.77, 3183,
                       4774.6, 6366.1, 7957.7, 15915,
                       31830, 111407, 190984, 350138, 509252,
                       560177.2, 1527756],
                "bi": [0.1, 0.36, 0.54,
                       0.99, 1.28, 1.36, 1.52,
                       1.58, 1.63, 1.67, 1.8,
                       1.9, 2, 2.1, 2.3, 2.5,
                       2.564, 3.78],
                "angle": 0.0}],
     "losses": {
         "f": [50, 100, 200, 400, 1000],
         "B": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1,
               1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8],
         "pfe":[[0.03, 0.07, 0.13, 0.22, 0.31, 0.43, 0.54, 0.68,
                 0.83, 1.01, 1.2, 1.42, 1.7, 2.12, 2.47, 2.8, 3.05, 3.25],
                [0.04, 0.16, 0.34, 0.55, 0.8, 1.08, 1.38, 1.73, 2.1, 2.51,
                 2.98, 3.51, 4.15, 4.97, 5.92],
                [0.09, 0.37, 0.79, 1.31, 1.91, 2.61, 3.39, 4.26, 5.23, 6.3,
                 7.51, 8.88, 10.5, 12.5, 14.9],
                [0.21, 0.92, 1.99, 3.33, 4.94, 6.84, 9, 11.4, 14.2, 17.3, 20.9,
                 24.9, 29.5, 35.4, 41.8],
                [0.99, 3.67, 7.63, 12.7, 18.9, 26.4, 35.4, 46, 58.4, 73, 90.1]]}
     },
    {"name": "M235-35A", "desc": "SURA", "ctype": 1, "fillfac": 1.0, "rho": 7.65,
     "curve": [{"hi": [0.0, 24.7, 32.6, 38.1, 43.1, 48.2, 53.9, 60.7, 68.8, 79.3, 93.7, 115.0,
                       156.0, 260.0, 690.0, 1950.0, 4410.0, 7630.0, 12000.0],
                "bi": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2,
                       1.3, 1.4, 1.5, 1.6, 1.7, 1.8], "angle": 0.0}],
     "losses": {"B": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8],
                "f": [50.0, 100.0, 200.0, 400.0, 1000.0, 2500.0],
                "pfe": [[0.02, 0.06, 0.111, 0.2, 0.29, 0.38, 0.5, 0.62, 0.77, 0.92, 1.1, 1.31, 1.56, 1.92, 2.25, 2.53, 2.75, 2.94],
                        [0.04, 0.14, 0.3, 0.49, 0.71, 0.97, 1.25, 1.57, 1.92, 2.31, 2.75, 3.26, 3.88, 4.67, 5.54],
                        [0.08, 0.32, 0.73, 1.21, 1.78, 2.44, 3.19, 4.03, 4.97, 6.01, 7.19, 8.54, 10.1, 12.2, 14.4],
                        [0.19, 0.87, 1.88, 3.17, 4.73, 6.56, 8.67, 11.0, 13.8, 16.9, 20.3, 24.3, 28.9, 34.8, 41.2],
                        [0.93, 3.55, 7.45, 12.3, 18.5, 25.8, 34.6, 45.0, 57.2, 71.5, 88.3],
                        [3.89, 14.3, 29.6, 50.2, 76.7, 110.0, 153.0, 205.0, 270.0, 349.0]]}}
    ]

machine = {
    "name": "VPM-8",
    "desc": "PM Motor 270mm 8 poles VMAGN",
    "poles": 8,
    "outer_diam": 0.26924,
    "bore_diam": 0.16192,
    "inner_diam": 0.11064,
    "airgap": 0.00075,
    "lfe": 0.08356,
    "stator": {
        "num_slots": 48,
        "mcvkey_yoke": "M19-29G",
        "fillfac": 0.95,
        "thcond": 24,
        "thcap": 480,
        "statorRotor3": {
            "slot_height": 0.0335,
            "slot_h1": 0.001,
            "slot_h2": 0.0,
            "slot_width": 0.00193,
            "slot_r1": 0.0001,
            "slot_r2": 0.00282,
            "wedge_width1": 0.00295,
            "wedge_width2": 0.0,
            "middle_line": 0.0,
            "tooth_width": 0.0,
            "slot_top_sh": 0.0}
    },
    "magnet": {
        "nodedist": 3,
        "material": "N36Z",
        "mcvkey_yoke": "M19-29G",
        "fillfac": 0.95,
        "thcond": 24,
        "thcap": 480,
        "magnetIronV": {
            "magn_angle": 145.0,
            "magn_height": 0.00648,
            "magn_width": 0.018,
            "condshaft_r": 0.05532,
            "magn_num": 1.0,
            "air_triangle": 1,
            "iron_hs": 0.0001,
            "gap_ma_iron": 0.0002,
            "iron_height": 0.00261,
            "magn_rem": 1.2,
            "iron_shape": 0.0802
        }
    },
    "windings": {
        "material": "Cu",
        "resistance": 0.0674,
        "num_phases": 3,
        "num_layers": 1,
        "num_wires": 9,
        "coil_span": 6,
        "cufilfact": 0.4,
        "culength": 1.4,
        "dia_wire": 1.5e-3,
        "num_par_wdgs": 1,
        "slot_indul": 1e-3
    }
}
