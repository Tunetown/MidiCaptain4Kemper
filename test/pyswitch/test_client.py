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
    "gc": MockGC()
}):
    from adafruit_midi.system_exclusive import SystemExclusive
    from adafruit_midi.control_change import ControlChange
    from lib.pyswitch.controller.Client import Client

    from.mocks_appl import *


class MockClient:
    def __init__(self):
        self.debug = False


class TestClient(unittest.TestCase):

    def test_set(self):
        midi = MockAdafruitMIDI.MIDI()
        
        client = Client(
            midi = midi,
            config = {}
        )

        mapping_1 = MockParameterMapping(
            set = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x01, 0x02, 0x03, 0x04]
            ),
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        client.set(mapping_1, 33)

        self.assertEqual(len(midi.messages_sent), 1)
        self.assertEqual(midi.messages_sent[0], mapping_1.set)
        self.assertEqual(mapping_1.set_value_calls, [33])


##############################################################################################


    def test_set_list(self):
        midi = MockAdafruitMIDI.MIDI()
        
        client = Client(
            midi = midi,
            config = {}
        )

        mapping_1 = MockParameterMapping(
            set = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x01, 0x02, 0x03, 0x04]
                ),
                None,
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x01, 0x02, 0x33, 0x04]
                ),
            ]
        )

        client.set(mapping_1, [33, 55])

        self.assertEqual(len(midi.messages_sent), 2)
        self.assertEqual(midi.messages_sent[0], mapping_1.set[0])
        self.assertEqual(midi.messages_sent[1], mapping_1.set[2])
        self.assertEqual(mapping_1.set_value_calls, [[33, 55]])


##############################################################################################


    def test_set_not_settable(self):        
        midi = MockAdafruitMIDI.MIDI()

        client = Client(
            midi = midi,
            config = {},
        )

        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        # Must not throw
        client.set(mapping_1, 33)

        
##############################################################################################


    def test_request(self):        
        midi = MockAdafruitMIDI.MIDI()

        client = Client(
            midi = midi,
            config = {},
        )

        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        listener = MockClientRequestListener()

        client.request(mapping_1, listener)

        self.assertEqual(len(midi.messages_sent), 1)
        self.assertEqual(midi.messages_sent[0], mapping_1.request)
        
        # Receive None
        client.receive(None)
        self.assertEqual(listener.parameter_changed_calls, [])

        # Receive ControlChange
        client.receive(ControlChange(3, 4))
        self.assertEqual(listener.parameter_changed_calls, [])

        # Receive correct message
        req = client.requests[0]
        answer_msg = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x20],
            data = [0x00, 0x00, 0x07, 0x45]
        )

        mapping_1.outputs_parse = [
            {
                "message": answer_msg,
                "value": 34
            }
        ]

        client.receive(answer_msg)
        self.assertEqual(listener.parameter_changed_calls, [mapping_1])
        self.assertEqual(mapping_1.value, 34)
        self.assertEqual(req.finished, True)
        self.assertEqual(client.requests, [])


##############################################################################################


    def test_request_list(self):        
        midi = MockAdafruitMIDI.MIDI()

        client = Client(
            midi = midi,
            config = {},
        )

        mapping_1 = MockParameterMapping(
            request = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                None,
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x24],
                    data = [0x05, 0x07, 0x79]
                )
            ],
            response = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x00, 0x00, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x00, 0x00, 0xa9]
                ),
                None,
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x23],
                    data = [0x00, 0x00, 0x07]
                )
            ]
        )

        answer_msg_1 = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x20],
            data = [0x00, 0x00, 0x07, 0x45]
        )

        answer_msg_2 = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x25],
            data = [0x00, 0x00, 0x07, 0x47]
        )

        answer_msg_3 = SystemExclusive(
            manufacturer_id = [0xbb, 0x10, 0x25],
            data = [0xaa, 0x00, 0x07, 0x47]
        )

        answer_msg_4 = SystemExclusive(
            manufacturer_id = [0xbb, 0x10, 0x25],
            data = [0xaa, 0x00, 0x07, 0x47]
        )

        mapping_1.outputs_parse = [
            {
                "message": answer_msg_1,
                "value": 33,
                "valueIndex": 0
            },
            {
                "message": answer_msg_2,
                "value": 22,
                "valueIndex": 1
            },
            {
                "message": answer_msg_3,
                "value": 34,
                "valueIndex": 2
            }
        ]

        mapping_1.output_result_finished = False

        listener = MockClientRequestListener()

        # Request value
        client.request(mapping_1, listener)
        req = client.requests[0]

        self.assertEqual(len(midi.messages_sent), 2)
        self.assertEqual(midi.messages_sent[0], mapping_1.request[0])
        self.assertEqual(midi.messages_sent[1], mapping_1.request[2])
        
        # Receive None
        client.receive(None)
        self.assertEqual(listener.parameter_changed_calls, [])

        # Receive ControlChange
        client.receive(ControlChange(3, 4))
        self.assertEqual(listener.parameter_changed_calls, [])
                
        # Receive unregistered message
        client.receive(answer_msg_4)
        self.assertEqual(listener.parameter_changed_calls, [])

        # Receive correct message 2 before 1
        client.receive(answer_msg_2)

        self.assertEqual(listener.parameter_changed_calls, [])
        self.assertEqual(mapping_1.value, [None, 22])

        self.assertEqual(req.finished, False)
        self.assertIn(req, client.requests)

        # Receive correct message 1
        client.receive(answer_msg_1)

        self.assertEqual(listener.parameter_changed_calls, [])
        self.assertEqual(mapping_1.value, [33, 22])
        
        self.assertEqual(req.finished, False)
        self.assertIn(req, client.requests)

        # Receive correct message 3 and finish
        mapping_1.output_result_finished = True
        client.receive(answer_msg_3)

        self.assertEqual(listener.parameter_changed_calls, [mapping_1])
        self.assertEqual(mapping_1.value, [33, 22, 34])        

        self.assertEqual(req.finished, True)
        self.assertEqual(client.requests, [])


##############################################################################################


    def test_request_endless(self):        
        midi = MockAdafruitMIDI.MIDI()

        client = Client(
            midi = midi,
            config = {
                "maxRequestLifetimeMillis": 0
            }
        )

        mapping_1 = MockParameterMapping(
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        listener = MockClientRequestListener()

        client.register(mapping_1, listener)

        answer_msg = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x20],
            data = [0x00, 0x00, 0x07, 0x45]
        )
        
        mapping_1.outputs_parse = [
            {
                "message": answer_msg,
                "value": 34
            }
        ]

        req = client.requests[0]

        client.receive(answer_msg)
        self.assertEqual(listener.parameter_changed_calls, [mapping_1])        
        
        self.assertEqual(mapping_1.value, 34)
        self.assertEqual(req.finished, False)
        self.assertTrue(req in client.requests)


##############################################################################################


    def test_request_terminate(self):        
        midi = MockAdafruitMIDI.MIDI()

        client = Client(
            midi = midi,
            config = {}
        )

        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        listener = MockClientRequestListener()

        client.request(mapping_1, listener)

        self.assertEqual(len(midi.messages_sent), 1)
        self.assertEqual(midi.messages_sent[0], mapping_1.request)
        
        req = client.requests[0]        
        req.terminate()
        self.assertEqual(req.finished, True)

        answer_msg = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x20],
            data = [0x00, 0x00, 0x07, 0x45]
        )

        mapping_1.outputs_parse = [
            {
                "message": answer_msg,
                "value": 34
            }
        ]

        client.receive(answer_msg)
        self.assertEqual(listener.parameter_changed_calls, [])
        self.assertEqual(mapping_1.value, None)
        
        self.assertEqual(client.requests, [])


##############################################################################################


    def test_mapping_eq_response(self):
        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        mapping_2 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x10]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        self.assertFalse(mapping_1 == None)
        self.assertFalse(None == mapping_2)

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.response.data[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.response.data[1] = 0x00
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.response.manufacturer_id[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_response_list(self):
        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x00, 0x00, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x30],
                    data = [0x77, 0x00, 0x09]
                )
            ]
        )

        mapping_2 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x10]
            ),
            response = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x00, 0x00, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x30],
                    data = [0x77, 0x00, 0x09]
                )
            ]
        )

        self.assertFalse(mapping_1 == None)
        self.assertFalse(None == mapping_2)

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.response[0].data[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.response[0].data[1] = 0x00
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.response[1].manufacturer_id[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_1.response[1].manufacturer_id[1] = 0x10
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.response = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x20],
            data = [0x00, 0x00, 0x09]
        )

        self.assertTrue(mapping_1 != mapping_2)

        mapping_1.response = [
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            ),
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x30],
                data = [0x77, 0x00, 0x09]
            ),
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x30],
                data = [0x77, 0x00, 0x09]
            )
        ]

        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_response_none(self):
        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            response = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x00, 0x00, 0x09]
            )
        )

        mapping_2 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_request(self):
        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        mapping_2 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        self.assertFalse(mapping_1 == None)
        self.assertFalse(None == mapping_2)

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.request.data[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.request.data[1] = 0x07
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.request.manufacturer_id[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_request_list(self):
        mapping_1 = MockParameterMapping(
            request = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x23],
                    data = [0x05, 0x77, 0x09]
                )
            ]
        )

        mapping_2 = MockParameterMapping(
            request = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x23],
                    data = [0x05, 0x77, 0x09]
                )
            ]
        )

        self.assertFalse(mapping_1 == None)
        self.assertFalse(None == mapping_2)

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.request[0].data[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.request[0].data[1] = 0x07
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.request[1].manufacturer_id[1] = 0x01
        self.assertTrue(mapping_1 != mapping_2)

        mapping_1.request[1].manufacturer_id[1] = 0x10
        self.assertTrue(mapping_1 == mapping_2)

        mapping_1.request = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x23],
            data = [0x05, 0x77, 0x09]
        )        
        self.assertTrue(mapping_1 != mapping_2)

        mapping_1.request = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x23],
                    data = [0x05, 0x77, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x23],
                    data = [0x05, 0x77, 0x09]
                )
            ]
        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_request_none(self):
        mapping_1 = MockParameterMapping(
            request = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )        )

        mapping_2 = MockParameterMapping()

        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_set(self):
        mapping_1 = MockParameterMapping(
            set = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        mapping_2 = MockParameterMapping(
            set = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.set.data[1] = 0x03
        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_set_list(self):
        mapping_1 = MockParameterMapping(
            set = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x24],
                    data = [0x05, 0x67, 0x09]
                )
            ]
        )

        mapping_2 = MockParameterMapping(
            set = [
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x20],
                    data = [0x05, 0x07, 0x09]
                ),
                SystemExclusive(
                    manufacturer_id = [0x00, 0x10, 0x24],
                    data = [0x05, 0x67, 0x09]
                )
            ]
        )

        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.set[1].data[1] = 0x03
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.set[1].data[1] = 0x67
        self.assertTrue(mapping_1 == mapping_2)

        mapping_2.set = SystemExclusive(
            manufacturer_id = [0x00, 0x10, 0x24],
            data = [0x05, 0x67, 0x09]
        )
        self.assertTrue(mapping_1 != mapping_2)

        mapping_2.et = [
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            ),
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x24],
                data = [0x05, 0x67, 0x09]
            ),
            SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x24],
                data = [0x05, 0x67, 0x09]
            )
        ]
        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_set_none(self):
        mapping_1 = MockParameterMapping(
            set = SystemExclusive(
                manufacturer_id = [0x00, 0x10, 0x20],
                data = [0x05, 0x07, 0x09]
            )
        )

        mapping_2 = MockParameterMapping()

        self.assertTrue(mapping_1 != mapping_2)


##############################################################################################


    def test_mapping_eq_all_none(self):
        mapping_1 = MockParameterMapping()
        mapping_2 = MockParameterMapping()

        self.assertTrue(mapping_1 != mapping_2)

