# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2026, TVB Widgets Team
#

import numpy
import pytest
from tvb.datatypes.connectivity import Connectivity

from tvbwidgets.ui.connectivity_ipy.global_context import CONTEXT
from tvbwidgets.ui.connectivity_ipy.operations import ConnectivityOperations

# The default connectivity lists the right hemisphere first, so its hemisphere order is not the identity
SELECTED = ['rA1', 'rA2', 'lAMYG']


def load_connectivity():
    conn = Connectivity.from_file()
    conn.configure()
    return conn


@pytest.fixture
def connectivity():
    return load_connectivity()


@pytest.fixture
def original():
    """An untouched copy of the same connectivity, used for the expected values"""
    return load_connectivity()


def run_operation(connectivity, description):
    CONTEXT.connectivity = connectivity
    operations = ConnectivityOperations()
    for checkbox in operations.regions_checkboxes:
        checkbox.value = checkbox.description in SELECTED
    node_operations, edge_operations = operations.children[3].children
    buttons = [*node_operations.children[1:], *edge_operations.children[1:]]
    next(button for button in buttons if button.description == description).click()
    return CONTEXT.connectivity


def indices(conn, labels):
    region_labels = list(conn.region_labels)
    return [region_labels.index(label) for label in labels]


def assert_regions_match(result, original):
    idx = indices(original, result.region_labels)
    assert numpy.array_equal(result.centres, original.centres[idx])
    assert numpy.array_equal(result.weights, original.weights[numpy.ix_(idx, idx)])
    assert numpy.array_equal(result.tract_lengths, original.tract_lengths[numpy.ix_(idx, idx)])


def assert_unchanged(connectivity, original):
    assert numpy.array_equal(connectivity.region_labels, original.region_labels)
    assert numpy.array_equal(connectivity.centres, original.centres)
    assert numpy.array_equal(connectivity.weights, original.weights)
    assert numpy.array_equal(connectivity.tract_lengths, original.tract_lengths)


def test_cut_unselected_regions(connectivity, original):
    result = run_operation(connectivity, 'Cut unselected regions')
    assert sorted(result.region_labels) == sorted(SELECTED)
    assert_regions_match(result, original)
    assert_unchanged(connectivity, original)


def test_cut_selected_regions(connectivity, original):
    result = run_operation(connectivity, 'Cut selected regions')
    assert sorted(result.region_labels) == sorted(set(original.region_labels) - set(SELECTED))
    assert_regions_match(result, original)
    assert_unchanged(connectivity, original)


def test_cut_unselected_edges(connectivity, original):
    result = run_operation(connectivity, 'Cut unselected edges')
    kept = numpy.ix_(indices(original, SELECTED), indices(original, SELECTED))
    expected = numpy.zeros_like(original.weights)
    expected[kept] = original.weights[kept]
    assert numpy.array_equal(result.region_labels, original.region_labels)
    assert numpy.array_equal(result.centres, original.centres)
    assert numpy.array_equal(result.weights, expected)
    assert numpy.array_equal(result.tract_lengths, original.tract_lengths)
    assert sorted(result.saved_selection) == sorted(indices(original, SELECTED))
    assert_unchanged(connectivity, original)


def test_cut_selected_edges(connectivity, original):
    result = run_operation(connectivity, 'Cut selected edges')
    cut = numpy.ix_(indices(original, SELECTED), indices(original, SELECTED))
    expected = original.weights.copy()
    expected[cut] = 0
    assert numpy.array_equal(result.region_labels, original.region_labels)
    assert numpy.array_equal(result.centres, original.centres)
    assert numpy.array_equal(result.weights, expected)
    assert numpy.array_equal(result.tract_lengths, original.tract_lengths)
    assert sorted(result.saved_selection) == sorted(indices(original, SELECTED))
    assert_unchanged(connectivity, original)
