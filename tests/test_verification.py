import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
from charging import Scenario,optimize,immediate,metrics,soc_from_power
from aging import evaluate,stress,prior_loss

class Verification(unittest.TestCase):
    def test_all_schedules_same_physics(self):
        a=Scenario();c=np.r_[np.full(16,.3),np.full(20,.1),np.full(12,.24)]
        schedules=[immediate(a)]+[optimize(c,a,*w)[0] for w in [(0,0),(1,0),(1,10)]]
        for p in schedules:
            m=metrics(p,c,a)
            for k in ['energy_residual_kwh','power_violation_kw','soc_violation','target_residual']:
                self.assertLess(m[k],1e-6)
            self.assertAlmostEqual(m['battery_kwh'],30,places=6)

    def test_flat_price_uniform_and_tie_break(self):
        a=Scenario();expected=a.grid_energy/(a.n*a.dt)
        for weights in [(1,0),(0,0)]:
            p,info=optimize(np.full(a.n,.2),a,*weights)
            np.testing.assert_allclose(p,expected,atol=1e-5)
            self.assertEqual(info['status'],'optimal')
            self.assertLess(info['max_constraint_residual'],1e-6)

    def test_price_optimum_known(self):
        a=Scenario();c=np.r_[np.full(16,.3),np.full(20,.1),np.full(12,.24)]
        p,info=optimize(c,a)
        self.assertAlmostEqual(c@p*a.dt,a.grid_energy*.1,places=6)
        self.assertLess(info['max_constraint_residual'],1e-6)

    def test_infeasible_and_invalid(self):
        with self.assertRaises(ValueError): immediate(Scenario(n=1))
        with self.assertRaises(ValueError): immediate(Scenario(efficiency=0))
        with self.assertRaises(ValueError): evaluate([.3,.8],.25,-.1)
        with self.assertRaises(ValueError): stress(.5,-5)

    def test_calendar_closed_form_and_units(self):
        k=1.2571e-5*.60225
        self.assertAlmostEqual(float(stress(.5)),k,places=15)
        for age in [0.,365.]:
            q=prior_loss(age)
            result=evaluate(np.full(49,.5),.25,q)
            exact=k*(np.sqrt(age*86400+43200)-np.sqrt(age*86400))
            self.assertAlmostEqual(result['calendar_increment_fraction'],exact,places=14)

    def test_history_split_and_timestep(self):
        # Identical physical linear path, subdivided; do not reoptimize here.
        a=evaluate(np.linspace(.3,.8,49),.25)
        b=evaluate(np.linspace(.3,.8,145),1/12)
        self.assertAlmostEqual(a['calendar_increment_fraction'],b['calendar_increment_fraction'],places=14)
        first=evaluate(np.linspace(.3,.55,25),.25)
        second=evaluate(np.linspace(.55,.8,25),.25,first['calendar_loss_final_fraction'])
        self.assertAlmostEqual(first['calendar_increment_fraction']+second['calendar_increment_fraction'],
                               a['calendar_increment_fraction'],places=14)

    def test_waiting_and_aging_history(self):
        s=soc_from_power(immediate(Scenario()),Scenario())
        full=evaluate(s,.25)
        self.assertGreater(full['calendar_increment_fraction'],evaluate(s[:21],.25)['calendar_increment_fraction'])
        self.assertGreater(evaluate(s,.25,0.)['calendar_increment_fraction'],full['calendar_increment_fraction'])

if __name__=='__main__':unittest.main(verbosity=2)
