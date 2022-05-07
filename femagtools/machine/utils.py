"""
  utils

  auxiliary module
"""
import numpy as np
import numpy.linalg as la
import logging

logger = logging.getLogger(__name__)


def K(d):
    """space phasor transformation matrix
    (Inverse Park Transformation) T-1 * dq
    arguments:
      d: rotation angle

    returns transformation matrix
    """
    return np.array((
        (-np.cos(d), np.sin(d)),
        (-np.cos(d-2*np.pi/3), np.sin(d-2*np.pi/3)),
        (-np.cos(d+2*np.pi/3), np.sin(d+2*np.pi/3))))


def T(d):
    """space phasor transformation matrix
    (Park Transformation) T * abc
    arguments:
      d: rotation angle

    returns transformation matrix
    """
    return np.array((
        (-np.cos(d), -np.cos(d-2*np.pi/3), -np.cos(d+2*np.pi/3)),
        (np.sin(d), np.sin(d-2*np.pi/3), np.sin(d+2*np.pi/3))))/3*2


def invpark(a, q, d):
    """ convert a dq vector to the abc reference frame
    (inverse park transformation)

    Args:
        a: rotation angle
        d: value in direct axis
        q: value in quadrature axis
    """
    if np.isscalar(a) and np.isscalar(q) and np.isscalar(d):
        return np.dot(K(a), (q, d))
    if np.isscalar(q) and np.isscalar(d):
        return np.array([K(x).dot((q, d)) for x in a]).T
    return np.array([K(x).dot((y, z)) for x, y, z in zip(a, d, q)]).T


KTH = 0.0039  # temperature coefficient of resistance
TREF = 20.0  # reference temperature of resistance


def kskinl(xi, nl):
    xi2 = 2*xi
    nl2 = nl*nl
    return 3 / (nl2*xi2)*(np.sinh(xi2) - np.sin(xi2)) / \
        (np.cosh(xi2)-np.cos(xi2)) + \
        ((nl2-1)/(nl2*xi)*(np.sinh(xi)+np.sin(xi)) /
            (np.cosh(xi)+np.cos(xi)))


def kskinr(xi, nl):
    xi2 = 2*xi
    nl2 = nl*nl
    return xi*((np.sinh(xi2)+np.sin(xi2))/(np.cosh(xi2)-np.cos(xi2))) + \
        ((nl2-1) / 3 * xi2*((np.sinh(xi)-np.sin(xi)) /
                            (np.cosh(xi)+np.cos(xi))))


def resistance(r0, w, temp, zeta, gam, nh):
    xi = zeta*np.sqrt(abs(w)/(2*np.pi)/(50*(1+KTH*(temp-TREF))))
    if np.isscalar(xi):
        if xi < 1e-12:
            k = 1
        else:
            k = (gam + kskinr(xi, nh)) / (1. + gam)
    else:
        k = np.ones(np.asarray(w).shape)
        k[xi > 1e-12] = (gam + kskinr(xi[xi > 1e-12], nh)) / (1. + gam)
    return r0*(1.+KTH*(temp - TREF))*k


def betai1(iq, id):
    """return beta and amplitude of dq currents"""
    logger.info("%s", (iq, id))
    return (np.arctan2(id, iq),
            la.norm((id, iq), axis=0)/np.sqrt(2.0))


def iqd(beta, i1):
    """return qd currents of beta and amplitude"""
    return np.sqrt(2.0)*i1*np.array([np.cos(beta),
                                     np.sin(beta)])


def puconv(dqpar, p, NR, UR, IR):
    """convert dqpar to per unit
    arguments:
    dqpar: dict from ld-iq or psid-psiq identification
    p: pole pairs
    NR: ref speed in 1/s
    UR: ref voltage per phase in V
    IR: ref current per phase in A
    """
    WR = 2*np.pi*NR*p
    PSIR = UR/WR
    SR = 3*UR*IR
    if 'beta' in dqpar:
        dqp = dict(beta=dqpar['beta'], losses=dict())
        dqp['i1'] = np.array(dqpar['i1'])/IR
    elif 'iq' in dqpar:
        dqp = dict(iq=np.array(dqpar['iq)'])/IR*np.sqrt(2), losses=dict())
        dqp['id'] = np.array(dqpar['id'])/IR*np.sqrt(2)
    else:
        raise ValueError('invalid dqpar')
    for k in 'psid', 'psiq':
        dqp[k] = np.array(dqpar[k])/PSIR
    if 'losses' in dqpar:
        for k in ('magnet', 'styoke_hyst', 'styoke_eddy',
                  'stteeth_hyst', 'stteeth_eddy', 'rotor_hyst', 'rotor_eddy'):
            dqp['losses'][k] = np.array(dqpar['losses'][k])/SR
        dqp['losses']['speed'] = p*dqpar['losses']['speed']/WR
        dqp['losses']['ef'] = dqpar['losses']['ef']
        dqp['losses']['hf'] = dqpar['losses']['hf']
    return dqp


def dqpar_interpol(xfit, dqpars, ipkey='temperature'):
    """return interpolated parameters at temperature or exc_current

    Arguments:
      xfit -- temperature or exc_current to fit dqpars
      dqpars -- list of dict with id, iq (or i1, beta), Psid and Psiq values
      ipkey -- key (string) to interpolate
    """
    # check current range
    ckeys = (('i1', 'beta'), ('id', 'iq'))
    dqtype = 0
    fpip = {k: dqpars[0][k] for k in ckeys[dqtype]}
    fpip['losses'] = dict()
    for k in ckeys[dqtype]:
        curr = np.array([f[k] for f in dqpars], dtype=object)
        shape = curr.shape
        if curr.shape != (len(dqpars), len(curr[0])):
            raise ValueError("current range conflict")
        curr = curr.astype(float)
        if not np.array([np.allclose(curr[0], c)
                         for c in curr[1:]]).all():
            raise ValueError("current range conflict")

    try:
        speed = np.array([d['losses']['speed'] for d in dqpars])
        if (np.max(speed) - np.min(speed))/np.mean(speed) > 1e-3:
            raise ValueError("losses: speed conflict")
    except KeyError:
        pass

    sorted_dqpars = sorted(dqpars, key=lambda d: d[ipkey])
    x = [f[ipkey] for f in sorted_dqpars]
    for k in ('psid', 'psiq'):
        m = np.array([f[k] for f in sorted_dqpars]).T
        if len(x) > 2:
            fpip[k] = np.array(
                [[ip.UnivariateSpline(x, y, k=2)(xfit)
                  for y in row] for row in m]).T
        else:
            fpip[k] = ip.interp1d(
                x, m, fill_value='extrapolate')(xfit).T
    try:
        for k in ('styoke_hyst', 'stteeth_hyst',
                  'styoke_eddy', 'stteeth_eddy',
                  'rotor_hyst', 'rotor_eddy',
                  'magnet'):
            m = np.array([f['losses'][k] for f in sorted_dqpars]).T
            if len(x) > 2:
                fpip['losses'][k] = np.array(
                    [[ip.UnivariateSpline(x, y, k=2)(xfit)
                      for y in row] for row in m]).T
            else:
                fpip['losses'][k] = ip.interp1d(
                    x, m, fill_value='extrapolate')(xfit).T
            fpip['losses']['speed'] = dqpars[0]['losses']['speed']
            for f in ('hf', 'ef'):
                if f in dqpars[0]['losses']:
                    fpip['losses'][f] = dqpars[0]['losses'][f]
    except KeyError:
        pass
    return x, fpip


def wdg_resistance(w1, l, d, sigma=56e3):
    """return winding resistance
    arguments:
    w1: number of turns
    l: wire length of one turn
    d: wire diameter m^2
    sigma: conductivity of wire material
    """
    a = np.pi*d**2/4
    return w1*l/sigma/a
