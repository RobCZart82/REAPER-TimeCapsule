"""Independent cycle oracle and synthetic MIDI dependency graph fixtures."""
import unittest
from unittest.mock import patch

from reaper_timecapsule.midi_validation import _action_cycles


def graph(edges, size):
    nodes = [(32060, str(i)) for i in range(size)]
    return {nodes[i]: {nodes[j] for a, j in edges if a == i}
            for i in range(size)}


def has_cycle_reference(adjacency):
    # Transitive closure, independent of DFS traversal and back-edge counting.
    reachable = {node: set(children) for node, children in adjacency.items()}
    for middle in adjacency:
        for node in adjacency:
            if middle in reachable[node]:
                reachable[node].update(reachable[middle])
    return any(node in children for node, children in reachable.items())


class MIDIGraphTests(unittest.TestCase):
    def assert_valid_witnesses(self, adjacency, cycles):
        for cycle in cycles:
            commands = cycle['commands']
            self.assertEqual(commands[0], commands[-1])
            self.assertEqual(cycle['length'], len(commands))
            for source, target in zip(commands, commands[1:]):
                self.assertIn((32060, target), adjacency[(32060, source)])

    def test_all_three_node_directed_graphs_against_closure(self):
        edges = [(i, j) for i in range(3) for j in range(3)]
        for mask in range(1 << len(edges)):
            adjacency = graph([edge for bit, edge in enumerate(edges)
                               if mask & (1 << bit)], 3)
            with self.subTest(mask=mask):
                cycles, count = _action_cycles(adjacency)
                self.assertEqual(count > 0, has_cycle_reference(adjacency))
                self.assertEqual(count, len(cycles))
                self.assert_valid_witnesses(adjacency, cycles)

    def test_disjoint_cycles_and_acyclic_cross_edge(self):
        adjacency = graph([(0, 1), (1, 0), (2, 3), (3, 2), (4, 1)], 5)
        cycles, count = _action_cycles(adjacency)
        self.assertEqual(count, 2)
        self.assert_valid_witnesses(adjacency, cycles)
        self.assertEqual(_action_cycles(graph([(0, 1), (0, 2), (2, 1)], 3)), ([], 0))

    def test_overlapping_cycles_count_back_edges_not_all_simple_cycles(self):
        # Three simple cycles, but this deterministic DFS has two back edges.
        adjacency = graph([(0, 1), (1, 0), (0, 2), (2, 0), (1, 2)], 3)
        cycles, count = _action_cycles(adjacency)
        self.assertEqual(count, 2)
        self.assert_valid_witnesses(adjacency, cycles)

    def test_deep_chain_and_capped_cycle_witness(self):
        nodes = [(32060, str(i).zfill(5)) for i in range(3000)]
        adjacency = {node: {nodes[i + 1]} if i + 1 < len(nodes) else set()
                     for i, node in enumerate(nodes)}
        self.assertEqual(_action_cycles(adjacency), ([], 0))
        adjacency[nodes[-1]].add(nodes[0])
        with patch('reaper_timecapsule.midi_validation.MAX_ISSUES', 5):
            cycles, count = _action_cycles(adjacency)
        self.assertEqual(count, 1)
        self.assertEqual(cycles[0]['length'], 3001)
        self.assertEqual(len(cycles[0]['commands']), 5)
        self.assertTrue(cycles[0]['truncated'])

    def test_detail_cap_keeps_complete_back_edge_count(self):
        adjacency = graph([(i, i) for i in range(10)], 10)
        with patch('reaper_timecapsule.midi_validation.MAX_ISSUES', 3):
            cycles, count = _action_cycles(adjacency)
        self.assertEqual(count, 10)
        self.assertEqual(len(cycles), 3)
        self.assert_valid_witnesses(adjacency, cycles)
