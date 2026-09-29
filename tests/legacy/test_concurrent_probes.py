import unittest

import numpy as np

from alpha_fix.engines.probes import BoundedProbeAlpha, compose_bounded_probes


class ConcurrentProbeCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = np.full((8, 12), 0.9, dtype=np.float32)

        left_jurisdiction = np.zeros_like(self.base, dtype=bool)
        left_jurisdiction[1:7, 1:7] = True
        left_keep = np.zeros_like(self.base, dtype=bool)
        left_keep[3:5, 4:6] = True
        left_alpha = np.ones_like(self.base)
        left_alpha[1:7, 1:7] = 0.25

        right_jurisdiction = np.zeros_like(self.base, dtype=bool)
        right_jurisdiction[2:7, 5:11] = True
        right_keep = np.zeros_like(self.base, dtype=bool)
        right_keep[4:6, 8:10] = True
        right_alpha = np.ones_like(self.base)
        right_alpha[2:7, 5:11] = 0.10

        self.left = BoundedProbeAlpha(left_alpha, left_jurisdiction, left_keep)
        self.right = BoundedProbeAlpha(right_alpha, right_jurisdiction, right_keep)

    def test_outside_union_is_bit_exact_baseline(self) -> None:
        result = compose_bounded_probes(self.base, (self.left, self.right))
        union = self.left.jurisdiction | self.right.jurisdiction
        self.assertTrue(np.array_equal(result[~union], self.base[~union]))

    def test_all_keep_masks_veto_every_probe(self) -> None:
        result = compose_bounded_probes(self.base, (self.left, self.right))
        keep_union = self.left.keep | self.right.keep
        self.assertTrue(np.array_equal(result[keep_union], self.base[keep_union]))

    def test_probe_order_is_irrelevant_even_when_jurisdictions_overlap(self) -> None:
        left_then_right = compose_bounded_probes(self.base, (self.left, self.right))
        right_then_left = compose_bounded_probes(self.base, (self.right, self.left))
        self.assertTrue(np.array_equal(left_then_right, right_then_left))

    def test_composition_is_monotone_and_idempotent(self) -> None:
        once = compose_bounded_probes(self.base, (self.left, self.right))
        twice = compose_bounded_probes(once, (self.left, self.right))
        self.assertTrue(np.all(once <= self.base))
        self.assertTrue(np.array_equal(once, twice))

    def test_shape_mismatch_is_rejected(self) -> None:
        bad = BoundedProbeAlpha(
            np.ones((2, 2), dtype=np.float32),
            np.ones((2, 2), dtype=bool),
            np.zeros((2, 2), dtype=bool),
        )
        with self.assertRaises(ValueError):
            compose_bounded_probes(self.base, (bad,))


if __name__ == "__main__":
    unittest.main()
