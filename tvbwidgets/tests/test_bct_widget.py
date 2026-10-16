# -*- coding: utf-8 -*-
#
# "TheVirtualBrain - Widgets" package
#
# (c) 2022-2025, TVB Widgets Team
#

import matplotlib
import numpy as np
import pytest
from plotly.basedatatypes import BaseFigure
from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.bct.bct_helper_widgets import ColoredConnectivityHeadWidget
from tvbwidgets.ui.bct.bct_metrics_data import BCT_METRICS, ANALYZER_GROUPS
from tvbwidgets.ui.bct.bct_metrics_widget import BCTMetricsProjectionWidget

matplotlib.use('Agg')

ANALYZER = "StrengthISOS"

@pytest.fixture(autouse=True)
def no_plotly_browser(monkeypatch):
    monkeypatch.setattr(BaseFigure, "show", lambda self, *args, **kwargs: None)

@pytest.fixture
def connectivity():
    conn = Connectivity.from_file()
    conn.configure()
    return conn

@pytest.fixture
def wid(connectivity):
    return BCTMetricsProjectionWidget(connectivity)

def edit_cell(wid, row, col, value):
    wid._editor_instance.new_connectivity.weights[row][col] = value

def run(wid, group="Degree and Similarity", analyzer=ANALYZER):
    wid._group_dropdown.value = group
    wid._analyzer_dropdown.value = analyzer
    wid._on_run(wid._run_btn)

def spy_analyzer(monkeypatch, analyzer=ANALYZER):
    used = []
    original = BCT_METRICS[analyzer]["fn"]

    def spy(conn):
        used.append(conn.weights.copy())
        return original(conn)

    monkeypatch.setitem(BCT_METRICS[analyzer], "fn", spy)
    return used

def test_conn_edited(wid, connectivity):
    assert wid.conn_edited is not connectivity
    assert np.array_equal(wid.conn_edited.weights, connectivity.weights)
    assert wid._source_text(wid.conn_edited) == "default weights"

    edit_cell(wid, 0, 1, 9.0)
    assert wid.conn_edited.weights[0][1] == 9.0
    assert connectivity.weights[0][1] != 9.0
    assert wid._source_text(wid.conn_edited) == "edited weights (1 cell(s) changed from default)"

def test_run_uses_edited_matrix(wid, monkeypatch):
    used = spy_analyzer(monkeypatch)
    edit_cell(wid, 0, 1, 9.0)
    run(wid)

    assert used[0][0][1] == 9.0
    assert "done" in wid._status.value
    assert not wid._run_btn.disabled

def test_self_loops_removed_only_for_analysis(wid, monkeypatch):
    used = spy_analyzer(monkeypatch)
    run(wid)

    assert not np.diag(used[0]).any()
    assert np.diag(wid.conn_edited.weights).any()

def test_negative_weights(wid, monkeypatch):
    used = spy_analyzer(monkeypatch)
    dialogs = []
    monkeypatch.setattr(wid, "_show_validation_dialog", lambda *args: dialogs.append(args))
    edit_cell(wid, 0, 1, -1.0)
    run(wid)
    assert len(dialogs) == 1
    assert "negative_weights" in dialogs[0][0]
    assert used == []

    wid._execute_analysis(wid.conn_edited, ANALYZER, ["negative_weights"])
    assert used[0][0][1] == 0
    assert wid.conn_edited.weights[0][1] == -1.0

def test_negative_weights_allowed_for_sign_analyzers(wid):
    weights = wid.conn_edited.weights.copy()
    weights[0][1] = -1.0
    assert "negative_weights" not in wid._validate_global(weights, "StrengthWeights")
    assert "negative_weights" in wid._validate_global(weights, ANALYZER)

def test_undirected_analyzer_on_directed_connectivity(wid, monkeypatch):
    used = spy_analyzer(monkeypatch, "Degree")
    run(wid, analyzer="Degree")
    assert "requires an undirected" in wid._undirected_warning.value
    assert wid._run_btn.disabled
    assert used == []

    wid._analyzer_dropdown.value = ANALYZER
    assert wid._undirected_warning.value == ""
    assert not wid._run_btn.disabled

def test_analysis_error(wid, monkeypatch):
    def failing(conn):
        raise ValueError("bad matrix")

    monkeypatch.setitem(BCT_METRICS[ANALYZER], "fn", failing)
    run(wid)
    assert "Error: bad matrix" in wid._status.value
    assert not wid._run_btn.disabled

@pytest.mark.parametrize("group, analyzer", [
    ("Modularity", "ModularityOCSM"),
    ("Density", "DensityDirected"),
    ("Degree and Similarity", "DegreeIOD"),
    ("Distance", "DistanceDBIN"),
    ("Centrality", "CentralityKCorenessBD"),
    ("Distance", "DistanceNETW"),
])
def test_result_types(wid, group, analyzer):
    run(wid, group, analyzer)
    assert f"{analyzer} done" in wid._status.value

def test_analysis_source_text(wid):
    lines = wid._analysis_source_lines(wid.conn_edited, ["self_loops", "negative_weights"])
    assert lines == ["<b>Analysis used the default weights, with self-self connections removed "
                     "and negative weights set to 0.</b>"]
    assert wid._analysis_source_lines(wid.conn_edited, []) == ["<b>Analysis used the default weights.</b>"]

def test_add_datatype(wid, connectivity):
    with pytest.raises(ValueError):
        wid.add_datatype("not a connectivity")

    editor = wid._editor_instance
    wid._status.value = "old status"
    wid.add_datatype(connectivity)
    assert wid._editor_instance is not editor
    assert wid._status.value == ""

def test_group_change(wid):
    wid._group_dropdown.value = "Density"
    assert list(wid._analyzer_dropdown.options) == ANALYZER_GROUPS["Density"]
    assert wid._analyzer_dropdown.value == "DensityDirected"
    assert "density" in wid._desc_label.value.lower()

def test_editor():
    widget = BCTMetricsProjectionWidget()
    assert isinstance(widget.connectivity, Connectivity)
    tab = widget._editor_instance.tab
    assert len(tab.children) == 1
    assert tab.get_title(0) == "weights"

def test_classify_component(wid):
    n = 76
    assert wid._classify_component(3.5, n, "density_dir", 0) == "scalar"
    assert wid._classify_component(np.ones(n), n, "strengths_dir", 0) == "per_node"
    assert wid._classify_component(np.ones(5), n, "erange", 0) == "network_vector"
    assert wid._classify_component(np.ones(n), n, "kcoreness_centrality_bd", 1) == "network_vector"
    assert wid._classify_component(np.ones((n, n)), n, "distance_bin", 0) == "matrix"
    assert wid._classify_component(np.ones((n, n, 2)), n, "findwalks", 0) == "tensor"

def test_colored_head_widget(connectivity):
    values = np.ones(76)
    values[0] = np.nan
    values[1] = np.inf
    head = ColoredConnectivityHeadWidget([connectivity], node_values=values)
    assert head._values[0] == 0
    assert head._values[1] == 0

    same = ColoredConnectivityHeadWidget([connectivity], node_values=np.full(76, 2.0))
    assert list(same._points_obj.color_range) == [1.5, 2.5]