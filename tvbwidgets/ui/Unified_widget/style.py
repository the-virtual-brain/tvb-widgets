_STYLE = """
<style>
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
.lsc-wrapper .lsc-select-nodes-column-title {
    font-weight: 600;
    margin-bottom: 6px;
}
.lsc-wrapper .lsc-select-nodes-close button {
    background: transparent !important;
    color: inherit !important;
    border: none !important;
    font-weight: 700 !important;
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