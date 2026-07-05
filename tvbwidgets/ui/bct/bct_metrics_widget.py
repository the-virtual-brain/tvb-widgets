
import numpy as np
import plotly.graph_objects as go
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import ipywidgets as widgets
import traceback
from IPython.display import display, clear_output

from tvb.datatypes.connectivity import Connectivity
from tvbwidgets.ui.base_widget import TVBWidget
from tvbwidgets import get_logger
from tvbwidgets.ui.bct.bct_metrics_data import BCT_METRICS, ANALYZER_GROUPS, NETWORK_VECTOR_OVERRIDES
from tvbwidgets.ui.bct.bct_helper_widgets import (
    BCTConnectivityMatrixEditor,
    BCTTractLengthsMatrixEditor,
    ColoredConnectivityHeadWidget,
)
from tvbwidgets.ui.bct.bct_compat import apply_bct_patches
apply_bct_patches()

LOGGER = get_logger(__name__)

class BCTMetricsProjectionWidget(TVBWidget):

    def __init__(self, connectivity=None, **kwargs):
        super().__init__(**kwargs)
        self.connectivity = connectivity if connectivity is not None else Connectivity.from_file()
        self._editor_instance = None
        self._build_ui()
        self._register_callbacks()
        self.logger.info("BCTMetricsProjectionWidget initialized.")

    def add_datatype(self, datatype):
        if not isinstance(datatype, Connectivity):
            self.logger.error("BCTMetricsProjectionWidget only accepts Connectivity datatypes.")
            raise ValueError(f"Expected Connectivity, got {type(datatype)}")
        self.connectivity = datatype
        self.logger.info(f"Connectivity updated: {datatype.gid.hex}")
        self._editor_instance = None
        with self._editor_output:
            clear_output(wait=True)
        with self._results_output:
            clear_output(wait=True)
        with self._dialog_output:
            clear_output(wait=True)

    def _build_ui(self):
        self._hint = widgets.HTML(
            "<span style='color:#888; font-size:12px'>"
            "Select an analyzer below to load the connectivity editor."
            "</span>"
        )

        group_names = list(ANALYZER_GROUPS.keys())
        self._group_label = widgets.HTML("<b>Analyzer group</b>")
        self._group_dropdown = widgets.Dropdown(
            options=group_names,
            layout=widgets.Layout(width="100%"),
        )

        first_group_analyzers = ANALYZER_GROUPS[group_names[0]] if group_names else []
        self._analyzer_label = widgets.HTML("<b>Analyzer</b>")
        self._analyzer_dropdown = widgets.Dropdown(
            options=first_group_analyzers,
            layout=widgets.Layout(width="100%"),
        )

        self._desc_label = widgets.HTML(value=self._current_description_html())

        self._load_btn = widgets.Button(
            description="Load",
            button_style="primary",
            icon="play",
            layout=widgets.Layout(width="160px", margin="8px 0"),
        )

        self._editor_output = widgets.Output()
        self._results_output = widgets.Output()
        self._dialog_output = widgets.Output()
        self._status = widgets.HTML("")

        self._run_btn = widgets.Button(
            description="Run analysis",
            button_style="primary",
            icon="play",
            layout=widgets.Layout(width="160px", margin="8px 0"),
        )

        self._divider = widgets.HTML("<hr style='margin: 12px 0; border-color: #ddd'>")

        self._ui = widgets.VBox([
            self._hint,
            self._group_label,
            self._group_dropdown,
            self._analyzer_label,
            self._analyzer_dropdown,
            self._desc_label,
            self._load_btn,
            self._divider,
            self._editor_output,
            self._divider,
            widgets.HBox([self._run_btn, self._status]),
            self._dialog_output,
            self._results_output,
        ], layout=widgets.Layout(padding="12px", gap="4px"))

    def _register_callbacks(self):
        self._group_dropdown.observe(self._on_group_change, names="value")
        self._analyzer_dropdown.observe(self._on_analyzer_change, names="value")
        self._load_btn.on_click(self._on_load)
        self._run_btn.on_click(self._on_run)

        with self._editor_output:
            display(widgets.HTML(
                "<span style='color:#888; font-size:12px'>"
                "Edit connectivity values, then hit Save before running."
                "</span>"
            ))

    def _on_group_change(self, change):
        new_group = change["new"]
        analyzers = ANALYZER_GROUPS.get(new_group, [])
        self._analyzer_dropdown.options = analyzers
        if analyzers:
            self._analyzer_dropdown.value = analyzers[0]
        self._desc_label.value = self._current_description_html()

    def _on_analyzer_change(self, change):
        self._desc_label.value = self._current_description_html()

    def _on_load(self, btn):
        self._status.value = ""
        self._show_editor(self.connectivity)
        with self._results_output:
            clear_output()
        with self._dialog_output:
            clear_output()

    def _on_run(self, btn):
        self._run_btn.disabled = True
        self._status.value = "<span style='color:orange'>Running...</span>"

        with self._results_output:
            clear_output(wait=True)
        with self._dialog_output:
            clear_output(wait=True)

        ed = self._editor_instance
        if ed is None:
            self._status.value = (
                "<span style='color:red'>Hit Load first to load the connectivity editor.</span>"
            )
            self._run_btn.disabled = False
            return

        connectivity = ed.get_connectivity()
        analyzer_name = self._analyzer_dropdown.value
        target_matrix = self._get_analyzer_matrix(connectivity, analyzer_name)

        issues = self._validate_global(target_matrix, analyzer_name)
        if issues:
            self._status.value = ""
            self._show_validation_dialog(issues, connectivity, analyzer_name)
            return

        analyzer_issues = self._validate_analyzer_specific(target_matrix, analyzer_name)
        if analyzer_issues:
            self._status.value = (
                "<span style='color:red'>This analyzer requires an undirected "
                "(symmetric) connectivity matrix, but the input matrix is directed. "
                "Edit the connectivity to symmetrize it, or pick an analyzer that "
                "supports directed input.</span>"
            )
            self._run_btn.disabled = False
            return

        self._execute_analysis(connectivity, analyzer_name)

    def _validate_global(self, weights, analyzer_name):
        issues = []
        if np.any(np.diag(weights) != 0):
            issues.append("self_loops")
        if not self._analyzer_allows_negative(analyzer_name):
            off_diag_mask = ~np.eye(weights.shape[0], dtype=bool)
            if np.any(weights[off_diag_mask] < 0):
                issues.append("negative_weights")
        return issues

    def _analyzer_allows_negative(self, analyzer_name):
        func_name = BCT_METRICS.get(analyzer_name, {}).get("func_name", "")
        return func_name.endswith("_sign")

    def _sanitize_weights(self, weights, issues):
        fixed = weights.copy()
        if "self_loops" in issues:
            np.fill_diagonal(fixed, 0)
        if "negative_weights" in issues:
            fixed[fixed < 0] = 0
        return fixed

    def _validation_dialog_text(self, issues):
        messages = []
        if "self_loops" in issues:
            messages.append(
                "Self-loops detected — the diagonal of the connectivity matrix has non-zero values."
            )
        if "negative_weights" in issues:
            messages.append(
                "Negative weights detected — this analyzer does not support negative weights."
            )
        return "<br>".join(messages)

    def _validation_fix_label(self, issues):
        if "self_loops" in issues and "negative_weights" in issues:
            return "Remove self-loops & negative weights, continue"
        elif "self_loops" in issues:
            return "Remove self-loops & continue"
        else:
            return "Remove negative weights & continue"

    def _show_validation_dialog(self, issues, connectivity, analyzer_name):
        message_html = widgets.HTML(
            "<div style='background:#3a3a3a; border:1px solid #555; "
            "border-radius:4px; padding:10px 14px; color:#ffffff; font-size:13px;'>"
            + self._validation_dialog_text(issues) +
            "</div>"
        )

        continue_btn = widgets.Button(
            description=self._validation_fix_label(issues),
            button_style="",
            layout=widgets.Layout(width="280px", margin="8px 8px 0 0"),
        )
        cancel_btn = widgets.Button(
            description="Cancel",
            button_style="",
            layout=widgets.Layout(width="100px", margin="8px 0 0 0"),
        )

        def _on_continue(b):
            with self._dialog_output:
                clear_output()
            matrix_attr = BCT_METRICS.get(analyzer_name, {}).get("matrix_attr", "weights")
            sanitized = self._sanitize_weights(getattr(connectivity, matrix_attr), issues)
            setattr(connectivity, matrix_attr, sanitized)
            self._execute_analysis(connectivity, analyzer_name)

        def _on_cancel(b):
            with self._dialog_output:
                clear_output()
            self._status.value = "<span style='color:gray'>Cancelled.</span>"
            self._run_btn.disabled = False

        continue_btn.on_click(_on_continue)
        cancel_btn.on_click(_on_cancel)

        dialog_box = widgets.VBox(
            [message_html, widgets.HBox([continue_btn, cancel_btn])],
            layout=widgets.Layout(
                border="1px solid #555",
                border_radius="4px",
                padding="10px",
                margin="8px 0",
                background="#2e2e2e",
            ),
        )

        with self._dialog_output:
            clear_output(wait=True)
            display(dialog_box)

    def _is_undirected(self, weights):
        return np.allclose(weights, weights.T)

    def _validate_analyzer_specific(self, weights, analyzer_name):
        issues = []
        requires_undirected = BCT_METRICS.get(analyzer_name, {}).get("undirected", False)
        if requires_undirected and not self._is_undirected(weights):
            issues.append("requires_undirected")
        return issues

    def _get_analyzer_matrix(self, connectivity, analyzer_name):
        matrix_attr = BCT_METRICS.get(analyzer_name, {}).get("matrix_attr", "weights")
        return getattr(connectivity, matrix_attr)

    def _execute_analysis(self, connectivity, analyzer_name):
        try:
            spec = BCT_METRICS[analyzer_name]
            raw_result = spec["fn"](connectivity)
            components = self._normalize_result(raw_result)

            with self._results_output:
                clear_output(wait=True)
                self._log_connectivity_diff(connectivity, analyzer_name)
                self._render_results(components, spec.get("labels", []), connectivity,
                                      analyzer_name, spec["func_name"])

            self._status.value = f"<span style='color:green'>{analyzer_name} done</span>"
            self.logger.info(f"Analysis complete: {analyzer_name}")

        except Exception as e:
            self._status.value = f"<span style='color:red'>Error: {e}</span>"
            self.logger.error(f"Error during BCT analysis: {e}")
            with self._results_output:
                print(traceback.format_exc())
        finally:
            self._run_btn.disabled = False

    def _normalize_result(self, raw):
        if isinstance(raw, (tuple, list)):
            return list(raw)
        return [raw]

    def _classify_component(self, value, num_regions, func_name, position):
        if (func_name, position) in NETWORK_VECTOR_OVERRIDES:
            return "network_vector"
        arr = np.asarray(value)
        if arr.ndim == 0:
            return "scalar"
        if arr.ndim == 1:
            return "per_node" if arr.shape[0] == num_regions else "network_vector"
        if arr.ndim == 2:
            return "matrix"
        return "tensor"

    def _render_results(self, components, labels, connectivity, analyzer_name, func_name):
        if len(labels) != len(components):
            labels = [f"Result {i + 1}" for i in range(len(components))]

        num_regions = connectivity.weights.shape[0]
        grouped = {"scalar": [], "per_node": [], "network_vector": [], "matrix": [], "tensor": []}
        for i, (label, value) in enumerate(zip(labels, components)):
            kind = self._classify_component(value, num_regions, func_name, i)
            grouped[kind].append((label, value))

        if grouped["scalar"]:
            self._render_scalars(grouped["scalar"])
        if grouped["per_node"]:
            self._render_per_node_group(grouped["per_node"], connectivity, analyzer_name)
        for label, value in grouped["network_vector"]:
            self._render_network_vector(label, value, analyzer_name)
        if grouped["matrix"]:
            self._render_matrix_group(grouped["matrix"], connectivity, analyzer_name)
        

    def _render_scalars(self, scalar_items):
        cards = []
        for label, value in scalar_items:
            try:
                display_value = f"{float(value):.4f}"
            except (TypeError, ValueError):
                display_value = str(value)
            cards.append(widgets.HTML(
                "<div style='display:inline-block; border:1px solid #444; "
                "padding:8px 14px; margin:4px;'>"
                f"<div>{label}</div>"
                f"<div>{display_value}</div>"
                "</div>"
            ))
        display(widgets.HBox(cards, layout=widgets.Layout(flex_flow="row wrap")))

    def _render_per_node_group(self, per_node_items, connectivity, analyzer_name):
        if len(per_node_items) == 1:
            label, values = per_node_items[0]
            self._render_single_per_node(values, connectivity, analyzer_name, label)
            return

        labels = [label for label, _ in per_node_items]
        values_by_label = dict(per_node_items)

        selector = widgets.Dropdown(
            options=labels,
            value=labels[0],
            description="Showing:",
            layout=widgets.Layout(width="60%"),
        )
        view_output = widgets.Output()

        def _render_selected(label):
            with view_output:
                clear_output(wait=True)
                self._render_single_per_node(values_by_label[label], connectivity, analyzer_name, label)

        def _on_select(change):
            _render_selected(change["new"])

        selector.observe(_on_select, names="value")
        _render_selected(labels[0])
        display(widgets.VBox([selector, view_output]))

    def _render_single_per_node(self, node_values, connectivity, analyzer_name, label):
        head_out = widgets.Output()
        hist_out = widgets.Output()

        with head_out:
            viz = ColoredConnectivityHeadWidget(
                [connectivity],
                node_values=node_values,
                region_labels=connectivity.region_labels,
            )
            viz.display()
            display(viz)

        with hist_out:
            self._plot_histogram(
                region_labels=connectivity.region_labels,
                node_values=node_values,
                analyzer_name=f"{analyzer_name} — {label}",
            )

        sub_tabs = widgets.Tab()
        sub_tabs.children = [head_out, hist_out]
        sub_tabs.set_title(0, "3D Head View")
        sub_tabs.set_title(1, "Histogram")
        display(sub_tabs)

    def _render_network_vector(self, label, vector, analyzer_name):
        vector = np.array(vector, dtype=float).ravel()
        mean_v = float(np.mean(vector))

        fig = go.Figure(go.Bar(
            x=list(range(len(vector))),
            y=vector.tolist(),
            marker=dict(
                color=vector.tolist(),
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title=label, tickfont=dict(color="#ccc"), titlefont=dict(color="#ccc")),
            ),
            hovertemplate="index: <b>%{x}</b><br>value: <b>%{y:.4f}</b><extra></extra>",
        ))
        fig.add_hline(
            y=mean_v,
            line=dict(color="#00e5ff", width=1.5, dash="dash"),
            annotation=dict(text=f"μ = {mean_v:.3f}", font=dict(color="#00e5ff", size=11),
                            xanchor="left", x=1.01, xref="paper"),
        )
        fig.update_layout(
            title=dict(text=f"<b>{analyzer_name}</b>  —  {label}",
                       font=dict(color="white", size=14, family="Arial"), x=0.5, xanchor="center"),
            paper_bgcolor="#1e1e2e",
            plot_bgcolor="#252535",
            xaxis=dict(title=dict(text="Index", font=dict(color="#aaa", size=12)),
                       tickfont=dict(color="#bbb"), gridcolor="rgba(255,255,255,0.06)"),
            yaxis=dict(title=dict(text=label, font=dict(color="#aaa", size=12)),
                       tickfont=dict(color="#bbb"), gridcolor="rgba(255,255,255,0.08)"),
            height=420,
            margin=dict(l=70, r=140, t=60, b=60),
        )
        fig.show()

    def _render_matrix_group(self, matrix_items, connectivity, analyzer_name):
        if len(matrix_items) == 1:
            label, matrix = matrix_items[0]
            self._render_single_matrix(matrix, connectivity, analyzer_name, label)
            return

        labels = [label for label, _ in matrix_items]
        matrices_by_label = dict(matrix_items)

        selector = widgets.Dropdown(
            options=labels,
            value=labels[0],
            description="Showing:",
            layout=widgets.Layout(width="60%"),
        )
        view_output = widgets.Output()

        def _render_selected(label):
            with view_output:
                clear_output(wait=True)
                self._render_single_matrix(matrices_by_label[label], connectivity, analyzer_name, label)

        def _on_select(change):
            _render_selected(change["new"])

        selector.observe(_on_select, names="value")
        _render_selected(labels[0])
        display(widgets.VBox([selector, view_output]))

    def _render_single_matrix(self, matrix, connectivity, analyzer_name, label):
        """NxN pairwise matrix -> square heatmap with region labels on both axes."""
        matrix = np.array(matrix, dtype=float)
        region_labels = list(connectivity.region_labels)
        n = len(region_labels)

        has_region_labels = matrix.shape == (n, n)
        if not has_region_labels:
            print(f"'{label}' has shape {matrix.shape}, expected ({n}, {n}) — "
                  "rendering without region labels.")
            x_labels = y_labels = None
        else:
            x_labels = y_labels = region_labels
        finite_vals  = matrix[np.isfinite(matrix)]
        has_negative = np.any(finite_vals < 0)
        colorscale   = "RdBu_r" if has_negative else "Viridis"
        p2, p98      = np.nanpercentile(finite_vals, [2, 98])

        fig = go.Figure(go.Heatmap(
            z=matrix,
            x=x_labels,
            y=y_labels,
            zmin=p2,
            zmax=p98,
            colorscale=colorscale,
            colorbar=dict(
                title=dict(text=label, font=dict(color="#ccc", size=11), side="right"),
                tickfont=dict(color="#ccc", size=10),
                thickness=16,
                len=0.85,
                outlinecolor="#555",
                outlinewidth=1,
            ),
            hovertemplate=(
                "Source: <b>%{y}</b><br>"
                "Target: <b>%{x}</b><br>"
                f"{label}: <b>%{{z:.4f}}</b><br>"
                "<extra></extra>"
            ),
        ))

        fig.update_layout(
            title=dict(
                text=f"<b>{analyzer_name}</b>  —  {label}",
                font=dict(color="white", size=14, family="Arial"),
                x=0.5, xanchor="center",
            ),
            paper_bgcolor="#1e1e2e",
            plot_bgcolor="#1e1e2e",
            xaxis=dict(
                title=dict(text="Target Region", font=dict(color="#aaa", size=12)),
                tickangle=-75,
                tickfont=dict(size=7, color="#bbb"),
                gridcolor="rgba(255,255,255,0.0)",
                linecolor="#555",
                automargin=True,
                constrain="domain",
            ),
            yaxis=dict(
                title=dict(text="Source Region", font=dict(color="#aaa", size=12)),
                tickfont=dict(size=7, color="#bbb"),
                gridcolor="rgba(255,255,255,0.0)",
                linecolor="#555",
                autorange="reversed",
                automargin=True,
                scaleanchor="x",
                scaleratio=1,
            ),
            margin=dict(l=130, r=130, t=70, b=100),
            height=700,
        )
        fig.show()

    def _current_description_html(self):
        analyzer_name = self._analyzer_dropdown.value if hasattr(self, "_analyzer_dropdown") else None
        if analyzer_name is None or analyzer_name not in BCT_METRICS:
            return "<i style='color:gray'><b>Select an analyzer to see its description.</b></i>"
        return f"<i style='color:gray'><b>{BCT_METRICS[analyzer_name]['description']}</b></i>"

    def _show_editor(self, connectivity):
        analyzer_name = self._analyzer_dropdown.value
        matrix_attr = BCT_METRICS.get(analyzer_name, {}).get("matrix_attr", "weights")
        editor_cls = BCTTractLengthsMatrixEditor if matrix_attr == "tract_lengths" else BCTConnectivityMatrixEditor

        with self._editor_output:
            clear_output(wait=True)
            ed = editor_cls(connectivity)
            self._editor_instance = ed
            ed.display()

    def _log_connectivity_diff(self, connectivity, analyzer_name):
        matrix_attr = BCT_METRICS.get(analyzer_name, {}).get("matrix_attr", "weights")
        current  = getattr(connectivity, matrix_attr)
        original = getattr(self.connectivity, matrix_attr)
        diff     = current - original
        changed  = np.argwhere(diff != 0)
        if len(changed) == 0:
            print(f"Using default {matrix_attr} (no edits detected)")
        else:
            print(f"Using edited {matrix_attr} — {len(changed)} cell(s) modified:")
            for row, col in changed:
                orig_val   = original[row, col]
                edited_val = current[row, col]
                label_row  = connectivity.region_labels[row]
                label_col  = connectivity.region_labels[col]
                print(f"  [{label_row}] → [{label_col}]  {orig_val:.4f} → {edited_val:.4f}")
        print("─" * 40)

    def _plot_histogram(self, region_labels, node_values, analyzer_name):
        """Region-indexed per-node values -> publication-style bar chart.
        """
        values = np.array(node_values, dtype=float)
        values[np.isinf(values)] = 0

        mean_val = float(np.mean(values))
        std_val  = float(np.std(values))
        min_val  = float(np.min(values))
        max_val  = float(np.max(values))
        sort_idx      = np.argsort(values)[::-1]
        sorted_vals   = values[sort_idx]
        sorted_labels = np.array(region_labels)[sort_idx]

        if min_val < mean_val < max_val:
            norm = mcolors.TwoSlopeNorm(vmin=min_val, vcenter=mean_val, vmax=max_val)
        elif min_val == max_val:
            norm = mcolors.Normalize(vmin=min_val - 0.5, vmax=max_val + 0.5)
        else:
            norm = mcolors.Normalize(vmin=min_val, vmax=max_val)
        cmap = cm.get_cmap("RdYlBu_r")
        bar_colors = [
            f"rgba({int(r*255)},{int(g*255)},{int(b*255)},{a:.2f})"
            for r, g, b, a in [cmap(norm(v)) for v in sorted_vals]
        ]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=list(sorted_labels),
            y=sorted_vals.tolist(),
            marker=dict(
                color=bar_colors,
                line=dict(color="rgba(255,255,255,0.12)", width=0.5),
            ),
            customdata=np.stack([sorted_labels, sorted_vals], axis=1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                f"{analyzer_name}: <b>%{{customdata[1]:.4f}}</b><br>"
                "<extra></extra>"
            ),
        ))
        fig.add_hrect(
            y0=mean_val - std_val,
            y1=mean_val + std_val,
            fillcolor="rgba(0,229,255,0.06)",
            line_width=0,
            annotation=dict(
                text="±1σ",
                font=dict(color="rgba(0,229,255,0.45)", size=10),
                xanchor="right",
                x=0,
                xref="paper",
            ),
        )

        fig.update_layout(
            title=dict(
                text=f"<b>{analyzer_name}</b>",
                font=dict(color="white", size=15, family="Arial"),
                x=0.5, xanchor="center",
            ),
            paper_bgcolor="#1e1e2e",
            plot_bgcolor="#252535",
            xaxis=dict(
                title=dict(text="Brain Region (sorted by value)", font=dict(color="#aaa", size=12)),
                tickangle=-75,
                tickfont=dict(size=7, color="#bbb"),
                gridcolor="rgba(255,255,255,0.05)",
                linecolor="#555",
                automargin=True,
            ),
            yaxis=dict(
                title=dict(
                    text=analyzer_name.split("—")[-1].strip(),
                    font=dict(color="#aaa", size=12),
                ),
                tickfont=dict(color="#bbb", size=10),
                gridcolor="rgba(255,255,255,0.07)",
                linecolor="#555",
                zeroline=True,
                zerolinecolor="rgba(255,255,255,0.12)",
            ),
            hoverlabel=dict(bgcolor="#1a1a2e", font_size=12, font_color="white"),
            margin=dict(l=70, r=120, t=60, b=120),
            height=560,
            dragmode="zoom",
            showlegend=False,
        )
        fig.update_xaxes(rangeslider=dict(visible=True, thickness=0.04, bgcolor="#333"))
        fig.show()

    def display(self):
        display(self._ui)