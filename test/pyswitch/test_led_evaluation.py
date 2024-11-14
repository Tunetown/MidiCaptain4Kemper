import sys
import unittest
from unittest.mock import patch   # Necessary workaround! Needs to be separated.

from .mocks_lib import *

# Import subject under test
with patch.dict(sys.modules, {
    "micropython": MockMicropython,
    "usb_midi": MockUsbMidi(),
    "adafruit_midi": MockAdafruitMIDI(),
    "adafruit_midi.control_change": MockAdafruitMIDIControlChange(),
    "adafruit_midi.system_exclusive": MockAdafruitMIDISystemExclusive(),
    "adafruit_midi.program_change": MockAdafruitMIDIProgramChange(),
    "adafruit_midi.midi_message": MockAdafruitMIDIMessage(),
    "adafruit_midi.start": MockAdafruitMIDIStart(),
    "adafruit_midi.midi_message": MockAdafruitMIDIMessage(),
    "gc": MockGC()
}):
    from lib.pyswitch.controller.Controller import Controller
    from .mocks_appl import *


class TestLedEvaluation(unittest.TestCase):

    #################################################################################################

    # Minimal call: Must not throw anything
    def test_no_switches(self):
        led_driver = MockNeoPixelDriver()

        appl = Controller(
            led_driver = led_driver,
            communication = {
                "valueProvider": MockValueProvider()
            },
            midi = MockMidiController(),
        )

        self.assertEqual(len(led_driver.leds), 0)
        self.assertEqual(len(appl.switches), 0)
        
    #################################################################################################

    def test_1_switch(self):
        led_driver = MockNeoPixelDriver()
        switch_1 = MockSwitch()

        appl = MockController(
            led_driver = led_driver,
            communication = {
                "valueProvider": MockValueProvider()
            },
            midi = MockMidiController(),
            switches = [
                {
                    "assignment": {
                        "model": switch_1,
                        "pixels": (0, 1, 2, 3, 8)
                    }
                }
            ]
        )

        self.assertEqual(len(led_driver.leds), 9)

    #################################################################################################

    def test_2_switches(self):
        led_driver = MockNeoPixelDriver()
        switch_1 = MockSwitch()
        switch_2 = MockSwitch()
        switch_3 = MockSwitch()

        appl = MockController(
            led_driver = led_driver,
            communication = {
                "valueProvider": MockValueProvider
            },
            midi = MockMidiController(),
            switches = [
                {
                    "assignment": {
                        "model": switch_1,
                        "pixels": (0, 1, 2, 3, 8)
                    }
                },
                {
                    "assignment": {
                        "model": switch_2
                    }
                },
                {
                    "assignment": {
                        "model": switch_3,
                        "pixels": (111, 2, 3)
                    }
                }
            ]
        )

        self.assertEqual(len(led_driver.leds), 112)
