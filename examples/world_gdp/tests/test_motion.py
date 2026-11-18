import unittest

from motion import monotone_slopes, sample_track


class MotionTests(unittest.TestCase):
    def test_exact_knots_and_no_overshoot(self):
        for values in ((10,20,40,60),(10,20,15,5),(0,0,30,0),(10,10,10,10)):
            slopes = monotone_slopes(values)
            for index, value in enumerate(values):
                self.assertEqual(sample_track(values,slopes,index),value)
            for index in range(len(values)-1):
                samples = [sample_track(values,slopes,index+step/100) for step in range(101)]
                self.assertTrue(all(min(values[index:index+2]) <= amount <= max(values[index:index+2]) for amount in samples))
                delta = values[index+1]-values[index]
                self.assertTrue(all((new-old)*delta >= -1e-10 for old,new in zip(samples,samples[1:])))

    def test_velocity_matches_at_same_trend_knot(self):
        values=(10,20,35,60)
        slopes=monotone_slopes(values)
        for index in (1,2):
            left=(sample_track(values,slopes,index)-sample_track(values,slopes,index-1e-5))/1e-5
            right=(sample_track(values,slopes,index+1e-5)-sample_track(values,slopes,index))/1e-5
            self.assertGreater(left,0)
            self.assertAlmostEqual(left,right,places=3)

    def test_reversal_has_zero_velocity_not_overshoot(self):
        self.assertEqual(monotone_slopes((10,20,15))[1],0)


if __name__ == '__main__':
    unittest.main()
