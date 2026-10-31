import importlib.util
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'CircuitPython-seeed xiao/BLE_Link/esc_protocol.py'
spec = importlib.util.spec_from_file_location('esc_protocol', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.driver = m.SimulatedESC()
        self.c = m.Controller(self.driver, lambda: self.now, 'session-a')
        self.rid = 0

    def command(self, cmd, **fields):
        self.rid += 1
        request = dict(id=self.rid, v=1, cmd=cmd, session='session-a')
        request.update(fields)
        return self.c.handle(request)

    def arm(self):
        self.assertTrue(self.command('ARM', throttle=0)['ok'])

    def test_startup_and_disarmed_output(self):
        self.assertEqual(self.driver.throttle, 0)
        self.assertFalse(self.command('SET_THROTTLE', throttle=500)['ok'])
        self.assertFalse(self.command('ARM', throttle=1)['ok'])
        self.arm()
        self.assertTrue(self.command('SET_THROTTLE', throttle=1000)['ok'])
        self.command('DISARM')
        self.assertEqual(self.driver.throttle, 0)

    def test_timeout_boundary_requires_rearm(self):
        self.arm()
        self.command('SET_THROTTLE', throttle=500)
        self.now = 1.499
        self.c.tick()
        self.assertEqual(self.driver.throttle, 500)
        self.now = 1.5
        self.c.tick()
        self.assertEqual(self.c.state, 'DISARMED')
        self.assertEqual(self.driver.throttle, 0)
        self.assertFalse(self.command('SET_THROTTLE', throttle=500)['ok'])

    def test_duplicate_never_renews_or_rearms(self):
        self.arm()
        req = dict(id=20, v=1, cmd='SET_THROTTLE', session='session-a', throttle=500)
        self.assertTrue(self.c.handle(req)['ok'])
        self.now = 1.0
        self.assertTrue(self.c.handle(req)['duplicate'])
        self.now = 1.5
        result = self.c.handle(req)
        self.assertTrue(result['duplicate'])
        self.assertEqual(result['control']['throttle'], 0)
        self.assertEqual(self.c.state, 'DISARMED')
        self.assertFalse(self.c.handle(dict(req, throttle=600))['ok'])

    def test_invalid_inputs_do_not_change_or_renew_output(self):
        self.arm()
        self.command('SET_THROTTLE', throttle=250)
        for value in [-1, 1001, True, None, '100', 1.5, float('nan'), float('inf')]:
            self.assertFalse(self.command('SET_THROTTLE', throttle=value)['ok'])
            self.assertEqual(self.driver.throttle, 250)
        for fields in [dict(session='old'), dict(v=True), dict(extra=1)]:
            self.assertFalse(self.command('SET_THROTTLE', throttle=500, **fields)['ok'])
        self.now = 1.5
        self.c.tick()
        self.assertEqual(self.driver.throttle, 0)

    def test_estop_latched_and_stale_stop_accepted(self):
        self.arm()
        self.command('SET_THROTTLE', throttle=500)
        self.assertTrue(self.c.handle(dict(id=0, cmd='ESTOP'))['ok'])
        self.assertEqual(self.driver.throttle, 0)
        self.assertFalse(self.command('ARM', throttle=0)['ok'])
        self.command('DISARM')
        self.assertEqual(self.c.state, 'ESTOP')
        self.assertFalse(self.command('RESET_ESTOP', session='old')['ok'])
        self.assertTrue(self.command('RESET_ESTOP')['ok'])
        self.assertEqual(self.c.state, 'DISARMED')
        self.arm()

    def test_disconnect_and_new_session_reject_old_commands(self):
        self.arm()
        self.command('SET_THROTTLE', throttle=500)
        self.c.disconnect()
        self.assertEqual(self.driver.throttle, 0)
        self.c = m.Controller(self.driver, lambda: self.now, 'session-b')
        self.assertFalse(self.command('ARM', throttle=0)['ok'])

    def test_status_text_and_malformed_do_not_renew(self):
        self.arm()
        self.command('SET_THROTTLE', throttle=500)
        for wire in [b'{', b'[]', b'null', b'\xff', b'{"id":true,"cmd":"ARM"}']:
            self.assertFalse(self.c.frame(wire)['ok'])
        self.assertTrue(self.c.frame(json.dumps(dict(id=10, text='hello')).encode())['ok'])
        self.assertTrue(self.command('STATUS')['ok'])
        self.now = 1.5
        self.c.tick()
        self.assertEqual(self.driver.throttle, 0)

    def test_unknown_and_invalid_id(self):
        for value in [True, -1, 2147483648, 1.0, None]:
            self.assertFalse(self.c.handle(dict(id=value, v=1, cmd='ARM', throttle=0))['ok'])
        self.assertFalse(self.command('FLY')['ok'])


if __name__ == '__main__':
    unittest.main()
