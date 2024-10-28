import sys
import unittest
from unittest.mock import patch   # Necessary workaround! Needs to be separated.

from .mocks_lib import *

with patch.dict(sys.modules, {
    "adafruit_midi.control_change": MockAdafruitMIDIControlChange(),
    "adafruit_midi.system_exclusive": MockAdafruitMIDISystemExclusive(),
}):
    from lib.pyswitch.ui.elements.DisplayElement import DisplayElement, DisplayBounds, HierarchicalDisplayElement


class MockDisplayElement(DisplayElement):
    def __init__(self, bounds = DisplayBounds(), name = "", id = 0):
        super().__init__(bounds, name, id)

        self.num_bounds_changed_calls = 0

    def bounds_changed(self):
        self.num_bounds_changed_calls += 1


class MockHierarchicalDisplayElement(HierarchicalDisplayElement):
    def __init__(self, bounds = DisplayBounds(), name = "", id = 0):
        super().__init__(bounds, name, id)

        self.num_bounds_changed_calls = 0

    def bounds_changed(self):
        super().bounds_changed()
        
        self.num_bounds_changed_calls += 1


###############################################################################################


class TestDisplayElement(unittest.TestCase):

    def test_bounds(self):
        b = DisplayBounds(20, 40, 100, 400)
        el = MockDisplayElement(
            bounds = b
        )

        self.assertEqual(el.bounds, b)

        b.x = 10
        self.assertNotEqual(el.bounds, b)
        self.assertEqual(el.num_bounds_changed_calls, 0)

        el.bounds = b
        self.assertEqual(el.bounds, b)
        self.assertEqual(el.num_bounds_changed_calls, 1)

        el.init(None, None)

        with self.assertRaises(Exception):
            el.bounds = DisplayBounds(0, 0, 20, 20)
            

    def test_search(self):
        el = DisplayElement(
            id = "foo"
        )

        self.assertEqual(el.search({ "id": "foo" }), el)
        self.assertEqual(el.search({ "id": "bar" }), None)


###############################################################################################


class TestHierarchicalDisplayElement(unittest.TestCase):

    def test_children(self):
        el = HierarchicalDisplayElement(
            id = "foo"
        )

        child_1 = HierarchicalDisplayElement(
            id = "bar"
        )

        child_2 = HierarchicalDisplayElement(
            id = "bat"
        )

        subchild_1 = HierarchicalDisplayElement(
            id = "tar"
        )

        el.add(child_1)
        el.add(child_2)

        child_1.add(None)
        child_1.add(subchild_1)
        child_1.add(None)

        # children
        self.assertEqual(el.children, [child_1, child_2])
        self.assertEqual(child_1.children, [None, subchild_1, None])
        self.assertEqual(child_2.children, [])
        self.assertEqual(subchild_1.children, [])

        # child(index)
        self.assertEqual(el.child(0), child_1)
        self.assertEqual(el.child(1), child_2)        
        self.assertEqual(child_1.child(0), None)
        self.assertEqual(child_1.child(1), subchild_1)

        with self.assertRaises(Exception):
            el.child(-1)

        with self.assertRaises(Exception):
            el.child(2)            

        # first_child / last_child
        self.assertEqual(el.first_child, child_1)
        self.assertEqual(el.last_child, child_2)

        self.assertEqual(child_1.first_child, subchild_1)
        self.assertEqual(child_1.last_child, subchild_1)        

        self.assertEqual(child_2.first_child, None)
        self.assertEqual(child_2.last_child, None)   


    def test_init(self):
        class Object:
            pass

        appl = Object()
        ui = Object()

        el = HierarchicalDisplayElement(
            id = "foo"
        )

        child_1 = HierarchicalDisplayElement(
            id = "bar"
        )

        child_2 = HierarchicalDisplayElement(
            id = "bat"
        )

        subchild_1 = HierarchicalDisplayElement(
            id = "tar"
        )

        el.add(child_1)
        el.add(child_2)

        child_1.add(None)
        child_1.add(subchild_1)

        self.assertEqual(el._initialized, False)
        self.assertEqual(child_1._initialized, False)
        self.assertEqual(child_2._initialized, False)
        self.assertEqual(subchild_1._initialized, False)

        el.init(ui, appl)

        self.assertEqual(el._initialized, True)
        self.assertEqual(child_1._initialized, True)
        self.assertEqual(child_2._initialized, True)
        self.assertEqual(subchild_1._initialized, True)
        

    def test_bounds_changed(self):
        class Object:
            pass

        appl = Object()
        ui = Object()

        el = MockHierarchicalDisplayElement(
            id = "foo"
        )

        child_1 = MockHierarchicalDisplayElement(
            id = "bar"
        )

        child_2 = MockHierarchicalDisplayElement(
            id = "bat"
        )

        subchild_1 = MockHierarchicalDisplayElement(
            id = "tar"
        )

        el.add(child_1)
        el.add(child_2)

        child_1.add(None)
        child_1.add(subchild_1)

        self.assertEqual(el.num_bounds_changed_calls, 0)
        self.assertEqual(child_1.num_bounds_changed_calls, 0)
        self.assertEqual(child_2.num_bounds_changed_calls, 0)
        self.assertEqual(subchild_1.num_bounds_changed_calls, 0)

        el.bounds_changed()

        self.assertEqual(el.num_bounds_changed_calls, 1)
        self.assertEqual(child_1.num_bounds_changed_calls, 1)
        self.assertEqual(child_2.num_bounds_changed_calls, 1)
        self.assertEqual(subchild_1.num_bounds_changed_calls, 1)
        

    def test_set(self):
        el = HierarchicalDisplayElement(
            id = "foo"
        )

        child_1 = HierarchicalDisplayElement(
            id = "bar"
        )

        child_2 = HierarchicalDisplayElement(
            id = "bat"
        )

        subchild_1 = HierarchicalDisplayElement(
            id = "tar"
        )

        el.add(child_1)
        el.set(child_2, 4)

        child_1.set(None, 2)
        child_1.add(subchild_1)

        self.assertEqual(el.children, [child_1, None, None, None, child_2])
        self.assertEqual(child_1.children, [None, None, None, subchild_1])
        self.assertEqual(child_2.children, [])
        self.assertEqual(subchild_1.children, [])

        with self.assertRaises(Exception):
            el.set(None, -1)


    def test_search(self):
        el = MockHierarchicalDisplayElement(
            id = "foo"
        )

        child_1 = MockHierarchicalDisplayElement(
            id = "bar"
        )

        child_2 = MockHierarchicalDisplayElement(
            id = "bat"
        )

        subchild_1 = MockHierarchicalDisplayElement(
            id = "tar"
        )

        el.add(child_1)
        el.add(child_2)

        child_1.add(None)
        child_1.add(subchild_1)

        # No index
        self.assertEqual(el.search({ "id": "none" }), None)
        self.assertEqual(el.search({ "id": "foo" }), el)
        self.assertEqual(el.search({ "id": "bar" }), child_1)
        self.assertEqual(el.search({ "id": "bat" }), child_2)
        self.assertEqual(el.search({ "id": "tar" }), subchild_1)

        # With index
        self.assertEqual(el.search({ "id": "foo", "index": -1 }), None)
        self.assertEqual(el.search({ "id": "foo", "index": 0 }), child_1)
        self.assertEqual(el.search({ "id": "foo", "index": 1 }), child_2)
        self.assertEqual(el.search({ "id": "foo", "index": 2 }), None)

        self.assertEqual(el.search({ "id": "bar", "index": -1 }), None)
        self.assertEqual(el.search({ "id": "bar", "index": 0 }), None)
        self.assertEqual(el.search({ "id": "bar", "index": 1 }), subchild_1)
        self.assertEqual(el.search({ "id": "bar", "index": 2 }), None)