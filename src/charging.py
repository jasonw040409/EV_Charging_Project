"""Deterministic charging QPs; powers are grid kW, SOC is a fraction."""
from dataclasses import dataclass
import time
import numpy as np
import cvxpy as cp

@dataclass(frozen=True)
class Scenario:
    n: int = 48
    dt: float = .25
    capacity: float = 60.
    initial: float = .3
    target: float = .8
    maximum_soc: float = .9
    maximum_power: float = 7.2
    efficiency: float = .9
    reference_soc: float = .7

    @property
    def grid_energy(self):
        return self.capacity * (self.target-self.initial) / self.efficiency

    def validate(self):
        if not (self.n > 0 and self.dt > 0 and self.capacity > 0 and
                0 < self.efficiency <= 1 and self.maximum_power > 0 and
                0 <= self.initial <= self.target <= self.maximum_soc <= 1 and
                0 <= self.reference_soc < 1):
            raise ValueError('Invalid physical parameters')
        if self.grid_energy > self.n*self.dt*self.maximum_power + 1e-9:
            raise ValueError('Infeasible energy requirement')


def soc_from_power(p, a):
    return np.r_[a.initial, a.initial + np.cumsum(p)*a.efficiency*a.dt/a.capacity]


def immediate(a):
    a.validate()
    return np.minimum(a.maximum_power, np.maximum(0, a.grid_energy/a.dt -
                      a.maximum_power*np.arange(a.n)))


def metrics(p, prices, a):
    s = soc_from_power(p, a)
    return dict(cost_dollars=float(np.dot(prices,p)*a.dt),
                power_proxy=float(np.mean((p/a.maximum_power)**2)),
                high_soc_proxy=float(np.mean((np.maximum(s[1:]-a.reference_soc,0)/
                                               (1-a.reference_soc))**2)),
                grid_kwh=float(sum(p)*a.dt), battery_kwh=float(sum(p)*a.dt*a.efficiency),
                peak_kw=float(max(p)), departure_soc=float(s[-1]),
                energy_residual_kwh=float(abs(sum(p)*a.dt-a.grid_energy)),
                power_violation_kw=float(max(0,-min(p),max(p)-a.maximum_power)),
                soc_violation=float(max(0,-min(s),max(s)-a.maximum_soc)),
                target_residual=float(abs(s[-1]-a.target)))


def optimize(prices, a, weight_power=0., weight_soc=0.):
    a.validate()
    prices=np.asarray(prices, dtype=float)
    if prices.shape != (a.n,) or not np.all(np.isfinite(prices)):
        raise ValueError('One finite price per interval required')
    if weight_power < 0 or weight_soc < 0:
        raise ValueError('Weights must be nonnegative')
    p=cp.Variable(a.n)
    z=cp.Variable(a.n, nonneg=True)
    s=a.initial+cp.cumsum(p)*a.efficiency*a.dt/a.capacity
    cons=[p>=0,p<=a.maximum_power,s>=0,s<=a.maximum_soc,
          cp.sum(p)*a.dt==a.grid_energy,z>=s-a.reference_soc,z<=1-a.reference_soc]
    cost=prices@p*a.dt
    cref=max(abs(float(prices@immediate(a)*a.dt)),1.)
    stress=weight_power*cp.sum_squares(p/a.maximum_power)/a.n + \
           weight_soc*cp.sum_squares(z/(1-a.reference_soc))/a.n
    # Cost-only: first solve LP, then minimize concentration within $1e-8 of optimum.
    started=time.perf_counter()
    options=dict(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=300)
    problem=cp.Problem(cp.Minimize(cost/cref+stress),cons)
    problem.solve(**options)
    if problem.status != 'optimal':
        raise RuntimeError(f'Solver failed: {problem.status}')
    stage_one_cost=float(cost.value)
    if weight_power==0 and weight_soc==0:
        cons=cons+[cost<=stage_one_cost+1e-8]
        problem=cp.Problem(cp.Minimize(cp.sum_squares(p/a.maximum_power)/a.n),cons)
        problem.solve(**options)
        if problem.status != 'optimal':
            raise RuntimeError(f'Tie-break failed: {problem.status}')
    residual=max(float(np.max(c.violation())) for c in cons)
    info=dict(status=problem.status, max_constraint_residual=residual,
              wall_seconds=time.perf_counter()-started,solver_seconds=problem.solver_stats.solve_time,
              iterations=problem.solver_stats.num_iters, stage_one_cost=stage_one_cost,
              weight_power=weight_power,weight_soc=weight_soc,cost_reference=cref)
    return np.asarray(p.value),info
