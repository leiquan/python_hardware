"""Exercise actual board serve/finally code with fake BLE streams, no radio imports."""
import ast
from pathlib import Path
import unittest
from test_esc_protocol import m, SOURCE


class FakeClock:
    now = 0
    def monotonic(self):
        return self.now
    def sleep(self, seconds):
        self.now += seconds


class RX:
    def __init__(self, clock, payload, failure=False):
        self.clock, self.payload, self.failure = clock, payload, failure
    @property
    def in_waiting(self):
        if self.failure:
            raise OSError('radio failure')
        return len(self.payload)
    def read(self, count):
        data, self.payload = self.payload[:count], self.payload[count:]
        return data


class TransportTests(unittest.TestCase):
    def setup_loop(self, payload=b'', failure=False):
        clock = FakeClock()
        class BLE:
            @property
            def connected(self):
                return clock.now < 2
        class TX:
            def write(self, data):
                pass
        class Service:
            rx = RX(clock, payload, failure)
            tx = TX()
        source = ast.parse((SOURCE.parent / 'code.py').read_text())
        names = {'serve', 'serve_session', 'pause', 'feed', 'reply', 'response_for'}
        module = ast.Module(body=[n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names], type_ignores=[])
        import json
        import os
        controller = m.Controller(m.SimulatedESC(), clock.monotonic, 'old')
        env = dict(Controller=m.Controller, SimulatedESC=m.SimulatedESC,
                   controller=controller, time=clock, os=os, json=json,
                   ENABLE_WATCHDOG=False, LinkLost=RuntimeError)
        exec(compile(module, 'board-loop', 'exec'), env)
        return clock, env, BLE(), Service()

    def test_partial_frame_times_out_throttle_without_waiting_for_newline(self):
        clock, env, ble, service = self.setup_loop(b'{"incomplete":')
        # Use serve_session to start already armed and test the actual idle loop.
        c = env['controller']
        c.handle(dict(id=1, v=1, cmd='ARM', session='old', throttle=0))
        c.handle(dict(id=2, v=1, cmd='SET_THROTTLE', session='old', throttle=800))
        env['serve_session'](ble, service)
        self.assertEqual(c.driver.throttle, 0)
        self.assertEqual(c.reason, 'command_timeout')

    def test_transport_exception_executes_disconnect_finally(self):
        _, env, ble, service = self.setup_loop(failure=True)
        with self.assertRaises(OSError):
            env['serve'](ble, service)
        self.assertEqual(env['controller'].reason, 'disconnect')
        self.assertEqual(env['controller'].driver.throttle, 0)

    def test_reconnect_rotates_session_and_preserves_estop(self):
        _, env, ble, service = self.setup_loop()
        env['controller'].stop('test', emergency=True)
        env['serve'](ble, service)
        self.assertNotEqual(env['controller'].session, 'old')
        self.assertEqual(env['controller'].state, 'ESTOP')
        self.assertEqual(env['controller'].driver.throttle, 0)
