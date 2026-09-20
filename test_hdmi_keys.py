import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hdmi_keys import Debouncer, validate
from unittest.mock import patch

class WatcherTests(unittest.TestCase):
    def test_baseline_both_states_is_silent(self):
        for state in (True, False):
            d = Debouncer()
            self.assertIsNone(d.update(state, 0))
            self.assertIsNone(d.update(state, 1.1))
            self.assertEqual(d.stable, state)

    def test_connect_disconnect_and_no_repeat(self):
        d = Debouncer()
        events = [d.update(state, t) for t, state in
                  [(0, False), (1.1, False), (2, True), (3.1, True),
                   (4, True), (5, False), (6.1, False), (7, False)]]
        self.assertEqual([e for e in events if e], ['KP_1', 'KP_2'])

    def test_noise_is_ignored(self):
        d = Debouncer()
        events = [d.update(state, t) for t, state in
                  [(0, False), (1.1, False), (2, True), (2.3, False),
                   (2.5, True), (2.8, False), (4, False)]]
        self.assertFalse(any(events))
        self.assertFalse(d.stable)

    def test_reconnect_has_new_silent_baseline(self):
        d = Debouncer()
        d.update(True, 0)
        d.update(True, 2)
        d = Debouncer()  # same reset used after USB read failure
        self.assertIsNone(d.update(False, 3))
        self.assertIsNone(d.update(False, 5))

    def test_only_expected_firmware_is_accepted(self):
        memory = {0xF800: 0xD7}
        for addr, data in [(0xCBD0, bytes.fromhex('5aa502000910')),
                           (0xCC04, b'D7LED01'), (0xCC00, bytes.fromhex('02cc80')),
                           (0xCC30, bytes.fromhex('02cc40'))]:
            memory.update({addr+i: value for i, value in enumerate(data)})
        with patch('hdmi_keys.read_byte', side_effect=lambda fd, addr: memory[addr]):
            validate(99)
            memory[0xCC04] = 0
            with self.assertRaises(RuntimeError):
                validate(99)

if __name__ == '__main__':
    unittest.main()
