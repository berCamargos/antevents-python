"""
Test the postgres adapters
"""
try:
    import psycopg2
    PREREQS_AVAILABLE = True
except ImportError:
    PREREQS_AVAILABLE = False
try:
    from config_for_tests import POSTGRES_DBNAME, POSTGRES_USER
except ImportError:
    POSTGRES_DBNAME=None
    POSTGRES_USER=None

# Set the following to True to skip the tearDown(). This is useful when
# trying to debug a failing test but should be left at False in
# production.
DEBUG_MODE = False

import asyncio
import unittest

from utils import ValueListSensor, SensorEventValidationSubscriber
from antevents.base import Scheduler, DefaultSubscriber
if PREREQS_AVAILABLE:
    from antevents.adapters.postgres import PostgresWriter, SensorEventMapping,\
        create_sensor_table, delete_sensor_table, PostgresReader
from antevents.linq.output import output
from antevents.linq.combinators import parallel


sensor_values = [1, 2, 3, 4, 5]

class CaptureSubscriber(DefaultSubscriber):
    def __init__(self):
        self.seq = []

    def on_next(self, x):
        self.seq.append(x)

            
    
@unittest.skipUnless(PREREQS_AVAILABLE, "postgress client library not installed")
@unittest.skipUnless(POSTGRES_DBNAME and POSTGRES_USER,
                     "POSTGRES_DBNAME and POSTGRES_USER not defined in config_for_tests")
class TestCase(unittest.TestCase):
    def setUp(self):
        self.mapping = SensorEventMapping('test_events')
        self.connect_string = "dbname=%s user=%s" % (POSTGRES_DBNAME,
                                                     POSTGRES_USER)
        conn = psycopg2.connect(self.connect_string)
        create_sensor_table(conn, 'test_events', drop_if_exists=True)
        conn.close()

    def tearDown(self):
        if DEBUG_MODE:
            print("DEBUG_MODE=True, SKIPPING tearDown()")
            return
        self.connect_string = "dbname=%s user=%s" % (POSTGRES_DBNAME,
                                                     POSTGRES_USER)
        conn = psycopg2.connect(self.connect_string)
        delete_sensor_table(conn, 'test_events')
        conn.close()
        
    def test_publish_and_subscribe(self):
        sensor = ValueListSensor(1, sensor_values)
        sensor.output()
        scheduler = Scheduler(asyncio.get_event_loop())
        pg = PostgresWriter(scheduler, self.connect_string, self.mapping)
        capture = CaptureSubscriber()
        scheduler.schedule_sensor_periodic(sensor, 0.5,
                                           parallel(pg, output, capture))
        scheduler.run_forever()
        print("finish writing to the database")
        row_source = PostgresReader(self.connect_string, self.mapping)
        row_source.output()
        validate = SensorEventValidationSubscriber(capture.seq, self)
        row_source.subscribe(validate)
        scheduler.schedule_recurring(row_source)
        scheduler.run_forever()
        self.assertTrue(validate.completed)
        print("finished reading rows")


if __name__ == '__main__':
    unittest.main()

