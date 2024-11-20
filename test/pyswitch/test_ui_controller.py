import sys
import unittest
from unittest.mock import patch   # Necessary workaround! Needs to be separated.

from .mocks_lib import *

with patch.dict(sys.modules, {
    "micropython": MockMicropython,
    "displayio": MockDisplayIO(),
    "adafruit_display_text": MockAdafruitDisplayText(),
    "adafruit_display_shapes.rect": MockDisplayShapes().rect(),
    "adafruit_midi.control_change": MockAdafruitMIDIControlChange(),
    "adafruit_midi.system_exclusive": MockAdafruitMIDISystemExclusive(),
    "adafruit_midi.program_change": MockAdafruitMIDIProgramChange(),
    "adafruit_midi.midi_message": MockAdafruitMIDIMessage(),
    "gc": MockGC()
}):
    from adafruit_midi.system_exclusive import SystemExclusive

    from lib.pyswitch.ui.UiController import UiController
    from lib.pyswitch.misc import Updater

    from .mocks_ui import *
    from .mocks_appl import *
    from .mocks_callback import *


class MockController2(Updater):
    def __init__(self):
        Updater.__init__(self)
        self.client = MockClient()


class MockUiController(UiController):
    def __init__(self, display_driver, font_loader, splash_callback = None):
        super().__init__(display_driver, font_loader, splash_callback)

        self.num_show_calls = 0

    def show(self):
        super().show()

        self.num_show_calls += 1


#########################################################################


class TestUiController(unittest.TestCase):

    def test(self):
        display_driver = MockDisplayDriver(300, 400)
        display_driver.init()

        font_loader = MockFontLoader()

        display = DisplayElement(id = 1)
        ui = UiController(display_driver, font_loader, MockSplashCallback(output = display))        

        appl = MockController2()
        ui.init(appl)

        ui.show()

        self.assertEqual(ui._current_splash_element.font_loader, font_loader)
        self.assertEqual(ui._current_splash_element, display)
        self.assertEqual(ui.bounds, DisplayBounds(0, 0, 300, 400))

        self.assertEqual(ui._current_splash_element._initialized, True)
        self.assertEqual(display_driver.tft.show_calls, [ui._current_splash_element.splash])


    def test_mappings(self):
        mapping_1 = MockParameterMapping(
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        mapping_2 = MockParameterMapping(
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x22],
                data = [0x00, 0x00, 0xe9]
            )
        )

        display_driver = MockDisplayDriver(300, 400, init = True)
        font_loader = MockFontLoader()

        display = DisplayElement(id = 1)
        ui = MockUiController(
            display_driver = display_driver, 
            font_loader = font_loader
        )

        cb = MockSplashCallback(
            output = display,
            mappings = [
                mapping_1,
                mapping_2
            ]
        )

        ui.set_callback(cb)

        appl = MockController2()
        ui.init(appl)

        ui.show()

        self.assertEqual(ui._current_splash_element.font_loader, font_loader)
        self.assertEqual(ui._current_splash_element, display)
        self.assertEqual(ui.bounds, DisplayBounds(0, 0, 300, 400))

        self.assertEqual(ui._current_splash_element._initialized, True)
        self.assertEqual(display_driver.tft.show_calls, [ui._current_splash_element.splash])

        self.assertEqual(appl.client.register_calls, [
            {
                "mapping": mapping_1,
                "listener": cb
            },
            {
                "mapping": mapping_2,
                "listener": cb
            }
        ])

        appl.update()

        self.assertEqual(appl.client.request_calls, [
            {
                "mapping": mapping_1,
                "listener": cb
            },
            {
                "mapping": mapping_2,
                "listener": cb
            }
        ])

        self.assertEqual(ui.num_show_calls, 1)
        
        ui.parameter_changed(None)

        self.assertEqual(ui.num_show_calls, 2)


    def test_add_updateables(self):
        display_driver = MockDisplayDriver(w = 300, h = 400, init = True)

        element_1 = DisplayElement(id = 1)
        element_2 = DisplayElement(id = 2)
        element_3 = MockUpdateableDisplayElement(id = 3)

        display = HierarchicalDisplayElement(
            children = [
                element_1,
                element_2,
                None,
                element_3
            ]
        )

        ui = UiController(display_driver, MockFontLoader(), MockSplashCallback(output = display))
        appl = MockController2()
        appl.add_updateable(ui)
        ui.init(appl)
        
        self.assertEqual(element_1._initialized, False)
        self.assertEqual(element_2._initialized, False)
        self.assertEqual(element_3._initialized, False)

        ui.show()

        self.assertEqual(element_1._initialized, True)
        self.assertEqual(element_2._initialized, True)
        self.assertEqual(element_3._initialized, True)

        appl.update()

        self.assertEqual(element_3.num_update_calls, 1)


    def test_error_show_before_init(self):
        display_driver = MockDisplayDriver(300, 400)
        display_driver.init()

        font_loader = MockFontLoader()

        element_1 = DisplayElement(id = 1)

        ui = UiController(display_driver, font_loader, MockSplashCallback(output = element_1))

        with self.assertRaises(Exception):
            ui.show()


