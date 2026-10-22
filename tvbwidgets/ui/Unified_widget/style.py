_STYLE = """
<style>
.lsc-wrapper {
    zoom: 0.8;
}
.lsc-wrapper .lsc-side-by-side {
    gap: 10px;
}
.lsc-wrapper .lsc-panel-title {
    font-weight: 700;
    font-size: 13px;
}
.lsc-wrapper .lsc-plot-details br {
    display: none;
}
.lsc-wrapper .lsc-plot-details .widget-html-content > div {
    display: grid;
    grid-template-columns: 1fr repeat(3, max-content max-content 1fr);
    gap: 4px 8px;
    align-items: baseline;
}
.lsc-wrapper .lsc-plot-details h3 {
    font-size: 12px;
    grid-column: 1 / -1;
    justify-self: center;
}
.lsc-wrapper .lsc-plot-details h4 {
    font-size: 11px;
    margin: 0;
}
.lsc-wrapper .lsc-plot-details p {
    font-size: 11px;
    margin: 0;
}
.lsc-wrapper .lsc-plot-details h4:nth-of-type(even) {
    grid-column: 5;
}
.lsc-wrapper .lsc-plot-details p:nth-of-type(even) {
    grid-column: 6;
}
.lsc-wrapper .lsc-plot-details h4:nth-of-type(odd) {
    grid-column: 8;
}
.lsc-wrapper .lsc-plot-details p:nth-of-type(odd) {
    grid-column: 9;
}
.lsc-wrapper .lsc-plot-details h4:first-of-type {
    grid-column: 2;
}
.lsc-wrapper .lsc-plot-details p:first-of-type {
    grid-column: 3;
}
.lsc-wrapper .lsc-tab-body {
    padding: 8px;
}
.lsc-wrapper .lsc-panel {
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background: #ffffff;
    overflow: visible;
    position: relative;
}
.lsc-wrapper .lsc-selection-bar {
    padding: 6px 8px;
    gap: 10px;
}
.lsc-wrapper .lsc-selection-label {
    font-weight: 600;
    font-size: 12px;
}
.lsc-wrapper .lsc-select-nodes-popup,
.lsc-wrapper .lsc-edge-operations-popup,
.lsc-wrapper .lsc-node-info-popup {
    background: #ffffff;
    border: 1px solid #c0c0c0;
    padding: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    z-index: 9999;
}
.lsc-wrapper .lsc-select-nodes-popup {
    position: absolute;
    max-height: calc(100vh - 120px);
    overflow: auto;
}
.lsc-wrapper .lsc-edge-operations-popup {
    position: absolute;
}
.lsc-wrapper .lsc-select-nodes-title {
    font-weight: 700;
    font-size: 14px;
}
.lsc-wrapper .lsc-select-nodes-close button {
    background: transparent !important;
    color: inherit !important;
    border: none !important;
    font-weight: 700 !important;
}
.lsc-wrapper .lsc-selection-name-field {
    position: relative;
    overflow: visible;
}
.lsc-wrapper .lsc-selection-error {
    position: absolute;
    top: 100%;
    left: 0;
    white-space: nowrap;
}
.lsc-wrapper .lsc-selection-error .widget-html-content {
    line-height: 16px;
}
.lsc-wrapper .lsc-btn button {
    border-radius: 3px !important;
}
.lsc-wrapper .widget-tab-contents,
.lsc-wrapper .p-TabPanel,
.lsc-wrapper .lsc-panel {
    overflow: visible !important;
    max-height: none !important;
    height: auto !important;
}
</style>
"""