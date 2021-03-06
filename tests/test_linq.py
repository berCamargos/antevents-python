# Copyright 2016 by MPI-SWS and Data-Ken Research.
# Licensed under the Apache 2.0 License.
"""Tests of the linq apis. Pretty much still manually verified, although running
it as a part of the automated test suite makes a decent regression test.
"""
import asyncio
import unittest

from antevents.base import *
from utils import make_test_publisher, make_test_publisher_from_vallist,\
                  ValidationSubscriber
import antevents.linq.where
import antevents.linq.output
import antevents.linq 
from antevents.linq.never import Never

def pp_buf(x):
    print("Buffered output: ", x)
    print("\n")


class TestLinq(unittest.TestCase):
    def test_case(self):
        """Rupak, if you want to test more, just add it here or add additional
        methods starting with test_
        """
        loop = asyncio.get_event_loop()
        
        s = make_test_publisher(1, stop_after_events=5)
 
        t = s.skip(2).some(lambda x: x[2]>100)

        s.subscribe(print)
        t.subscribe(print)

        scheduler = Scheduler(loop)
        scheduler.schedule_periodic(s, 2) # sample once every 2 seconds


        u = s.take_last(3).scan(lambda a, x: a+x[2], 0)
        u.subscribe(print)
        v = s.take_last(3).reduce(lambda a, x: a+x[2], 0)
        v.subscribe(print)

        w = s.buffer_with_time(5, scheduler)
        w.subscribe(pp_buf)
        # w = Never()
        # w.subscribe(print)
        # scheduler.schedule_periodic(w, 1)

        s.print_downstream()

        loop.call_later(30, scheduler.stop)

        scheduler.run_forever()
        print("That's all folks")

    def test_first(self):
        """Test the first() operator
        """
        p = make_test_publisher_from_vallist(1, [1, 2, 3, 4, 5, 6])
        vs = ValidationSubscriber([1], self)
        p.first().subscribe(vs)
        scheduler = Scheduler(asyncio.get_event_loop())
        scheduler.schedule_recurring(p)
        scheduler.run_forever()
        self.assertTrue(vs.completed)
        
        
if __name__ == '__main__':
    unittest.main()

