"""Naumann calendar capacity fade, full-text verified against author's thesis.

No cycling damage is predicted. Fractional loss; seconds; kelvin.
Exact virtual-time continuation: q_new^2 = q_old^2 + integral(k^2 dt).
Four-node Gauss integration is exact for the degree-six SOC polynomial at
constant temperature and piecewise-linear SOC (constant power per slot).
"""
import numpy as np

K_REF=1.2571e-5  # fraction / sqrt(second); thesis table is percent, divide by 100
EA=17126.      # J/mol
R=8.314       # J/(mol K), author's convention
T_REF=298.15


def stress(soc, temperature_c=25.):
    s=np.asarray(soc)
    if np.any(~np.isfinite(s)) or np.any((s<0)|(s>1)) or not 0<=temperature_c<=60:
        raise ValueError('Calendar model restricted to SOC 0..1 and T 0..60 C')
    return K_REF*np.exp(-EA/R*(1/(temperature_c+273.15)-1/T_REF))*\
           (2.8575*(s-.5)**3+.60225)


def prior_loss(days=365., soc=.5, temperature_c=25.):
    if not np.isfinite(days) or days<0:
        raise ValueError('Age must be nonnegative')
    return float(stress(soc,temperature_c)*np.sqrt(days*86400))


def evaluate(soc, dt_hours, initial_calendar_loss=None, temperature_c=25.):
    s=np.asarray(soc,dtype=float)
    if s.ndim!=1 or len(s)<2 or dt_hours<=0:
        raise ValueError('SOC boundaries and a positive interval required')
    stress(s,temperature_c)
    q0=prior_loss() if initial_calendar_loss is None else initial_calendar_loss
    if not np.isfinite(q0) or q0<0:
        raise ValueError('Nonnegative accumulated calendar loss required')
    nodes,weights=np.polynomial.legendre.leggauss(4)
    samples=s[:-1,None]+(s[1:]-s[:-1])[:,None]*(nodes+1)/2
    increments=np.sum(stress(samples,temperature_c)**2*weights/2,axis=1)*dt_hours*3600
    integral=float(sum(increments))
    q1=float(np.sqrt(q0*q0+integral))
    # Stable subtraction for small increments on an already aged cell.
    delta=integral/(q1+q0) if q1+q0 else 0.
    return dict(calendar_loss_initial_fraction=float(q0),calendar_loss_final_fraction=q1,
                calendar_increment_fraction=delta,calendar_increment_ppm=delta*1e6,
                temperature_c=temperature_c)
