import femagtools.machine
import femagtools.machine.pm
import femagtools.machine.sm
import femagtools.machine.im
import numpy as np
import copy
import scipy.interpolate as ip
import logging
from .utils import betai1, dqpar_interpol

logger = logging.getLogger("femagtools.effloss")


def _create_machine(temp, eecpars):
    """create machine according to the eecpars:
    PM, EESM or IM"""
    if 'ldq' in eecpars:  # this is a PM (or EESM)
        if (isinstance(eecpars['ldq'], list) and
            'ex_current' in eecpars['ldq'][0] or
            isinstance(eecpars['ldq'], dict) and
                'ex_current' in eecpars['ldq']):
            pars = copy.deepcopy(eecpars)
            pars['tcu1'] = temp[0]
            pars['tcu2'] = temp[1]
            return femagtools.machine.sm.SynchronousMachine(pars)

        if isinstance(eecpars['ldq'], list) and len(eecpars['ldq']) > 1:
            x, dqp = dqpar_interpol(
                temp[1], eecpars['ldq'], ipkey='temperature')
        else:
            dqp = eecpars['ldq'][0]
            logger.warning(
                "single temperature DQ parameters: unable to fit temperature %s", temp)
        return femagtools.machine.PmRelMachineLdq(
            eecpars['m'], eecpars['p'], r1=eecpars['r1'],
            ls=eecpars['ls1'],
            psid=dqp['psid'],
            psiq=dqp['psiq'],
            losses=dqp['losses'],
            beta=dqp['beta'],
            i1=dqp['i1'],
            tcu1=temp[0])
    else:  # must be an induction machine
        pars = copy.deepcopy(eecpars)
        pars['tcu1'] = temp[0]
        pars['tcu2'] = temp[1]
        return femagtools.machine.im.InductionMachine(pars)


def _generate_mesh(n, T, nb, Tb, npoints):
    """return speed and torque list for driving/braking speed range

    arguments:
    n: list of speed values in driving mode (1/s)
    T: list of torque values in driving mode (Nm)
    nb: list of speed values in braking mode (1/s)
    Tb: list of torque values in braking mode (Nm)
    npoints: number of values for speed and torque list
    """
    if nb:
        nmax = 0.99*min(max(n), max(nb))
        tmin, tmax = min(Tb), max(T)
        tnum = npoints[1]//2
    else:
        nmax = max(n)
        tmin, tmax = 0, max(T)
        tnum = npoints[1]
    tip = ip.interp1d(n, T)
    if nb and Tb:
        tbip = ip.interp1d(nb, Tb)
    else:
        def tbip(x): return 0

    nxtx = []
    for nx in np.linspace(1, nmax, npoints[0]):
        t0 = tbip(nx)
        t1 = tip(nx)
        try:
            npnts = round((t1-t0) / (tmax-tmin) * npoints[1])
            if npnts > 2:
                for t in np.concatenate(
                        (np.linspace(t0, 0.015*tmin, tnum),
                         np.linspace(0.015*tmax, t1, tnum))):
                    nxtx.append((nx, t))
        except ValueError as ex:
            logger.warning("n, t0, t1 %s tmin, tmax %s, npoints %d",
                           (n, t0, t1), (tmin, tmax), npoints[1])
    return np.array(nxtx).T


def efficiency_losses_map(eecpars, u1, T, temp, n, npoints=(50, 40)):
    """return speed, torque efficiency and losses

    arguments:
    eecpars: (dict) EEC Parameter with
      dicts at different temperatures (or machine object)
    u1: (float) phase voltage (V rms)
    T: (float) starting torque (Nm)
    temp: temperature (°C)
    n: (float) maximum speed (1/s)
    npoints: (list) number of values of speed and torque

    """
    if isinstance(eecpars, dict):
        if isinstance(temp, list) or isinstance(temp, tuple):
            xtemp = [temp[0], temp[1]]
        else:
            xtemp = [temp, temp]
        m = _create_machine(xtemp, eecpars)
    else:  # must be a Machine
        m = eecpars
    if isinstance(T, list):
        r['T'] = T
        r['n'] = n
        rb['T'] = []
        rb['n'] = []
    else:
        nmax = n
        r = m.characteristics(T, nmax, u1)  # driving mode
        rb = m.characteristics(-T, max(r['n']), u1)  # braking mode

    ntmesh = _generate_mesh(r['n'], r['T'],
                            rb['n'], rb['T'], npoints)

    if 'ldq' in eecpars:
        iqd = np.array([
            m.iqd_torque_umax(
                nt[1],
                2*np.pi*nt[0]*m.p,
                u1)[:-1]
            for nt in ntmesh.T]).T
        beta, i1 = betai1(iqd[0], iqd[1])
        uqd = [m.uqd(2*np.pi*n*m.p, *i)
               for n, i in zip(ntmesh[0], iqd.T)]
        u1 = np.linalg.norm(uqd, axis=1)/np.sqrt(2.0)
        f1 = ntmesh[0]*m.p
    else:
        f1 = []
        u1max = u1
        r = dict(u1=[], i1=[], plfe1=[], plcu1=[], plcu2=[])
        for n, tq in ntmesh.T:
            wm = 2*np.pi*n
            w1 = m.w1(u1max, m.psiref, tq, wm)
            f1.append(w1/2/np.pi)
            u1 = m.u1(w1, m.psi, wm)
            r['u1'].append(np.abs(u1))
            i1 = m.i1(w1, m.psi, wm)
            r['i1'].append(np.abs(i1))
            r['plfe1'].append(m.m*np.abs(u1)**2/m.rfe(w1, m.psi))
            i2 = m.i2(w1, m.psi, wm)
            r['plcu1'].append(m.m*np.abs(i1)**2*m.rstat(w1))
            r['plcu2'].append(m.m*np.abs(i2)**2*m.rrot(w1-m.p*wm))

    tfric = eecpars['kfric_b']*eecpars['rotor_mass']*30e-3/np.pi
    plfric = 2*np.pi*ntmesh[0]*tfric
    ntmesh[1] -= tfric
    pmech = np.array(
        [2*np.pi*nt[0]*nt[1]
         for nt in ntmesh.T])

    if 'ldq' in eecpars:
        plfe1 = m.iqd_plfe1(*iqd, f1)
        plfe2 = m.iqd_plfe2(iqd[0], iqd[1], f1)
        plmag = m.iqd_plmag(iqd[0], iqd[1], f1)
        plcu1 = m.iqd_plcu1(iqd[0], iqd[1], 2*np.pi*f1)
        plcu2 = m.iqd_plcu2(*iqd)
    else:
        plfe1 = np.array(r['plfe1'])
        plfe2 = np.zeros(ntmesh.shape[1])
        plmag = np.zeros(ntmesh.shape[1])
        plcu1 = np.array(r['plcu1'])
        plcu2 = np.array(r['plcu2'])
        iqd = np.zeros(ntmesh.shape)
        u1 = np.array(r['u1'])
        i1 = np.array(r['i1'])

    ploss = plfe1+plfe2+plmag+plcu1+plcu2+plfric

    eta = []
    for pm, pl in zip(pmech, ploss):
        p1 = pm+pl
        if (p1 <= 0 and pm >= 0) or (p1 >= 0 and pm <= 0):
            e = 0
        elif abs(p1) > abs(pm):
            e = pm / p1
        else:
            e = p1 / pm
        eta.append(e)

    return dict(
        iq=iqd[0].tolist(),
        id=iqd[1].tolist(),
        i1=i1.tolist(),
        u1=u1.tolist(),
        n=ntmesh[0].tolist(),
        T=ntmesh[1].tolist(),
        pmech=pmech.tolist(),
        eta=eta,
        plfe1=plfe1.tolist(),
        plfe2=plfe2.tolist(),
        plmag=plmag.tolist(),
        plcu1=plcu1.tolist(),
        plcu2=plcu2.tolist(),
        plfric=plfric.tolist(),
        losses=ploss.tolist())
