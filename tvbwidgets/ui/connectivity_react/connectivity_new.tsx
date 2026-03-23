// @ts-nocheck
import * as React from "react";
import { cluster, hierarchy } from "https://esm.sh/d3-hierarchy@3";
import { lineRadial, curveBundle } from "https://esm.sh/d3-shape@3";

const COLOR_DEFAULT       = "rgba(74, 144, 217, 0.18)";
const COLOR_OUTGOING      = "rgba(231, 76,  60,  0.85)";
const COLOR_INCOMING      = "rgba(46,  204, 113, 0.85)";
const COLOR_DIM           = "rgba(180, 180, 180, 0.04)";
const COLOR_NODE_DEFAULT  = "#555";
const COLOR_NODE_SELECTED = "#f39c12";

const WIDTH  = 800;
const HEIGHT = 800;
const RADIUS = 280;
const CX     = WIDTH  / 2;
const CY     = HEIGHT / 2;

const STYLES = {
  root: {
    display: "flex", flexDirection: "column", alignItems: "center",
    gap: "10px", padding: "12px", background: "#f7f7f7",
    borderRadius: "8px", fontFamily: "Arial, sans-serif",
  },
  controls: { display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap", justifyContent: "center" },
  btnBase: {
    padding: "6px 20px", border: "2px solid #4a90d9", borderRadius: "20px",
    background: "white", color: "#4a90d9", fontSize: "13px",
    fontWeight: "600", cursor: "pointer",
  },
  btnActive: { background: "#4a90d9", color: "white" },
  btnClear: {
    padding: "5px 14px", border: "1.5px solid #e74c3c", borderRadius: "20px",
    background: "white", color: "#e74c3c", fontSize: "12px", cursor: "pointer",
  },
  sliderRow: {
    display: "flex", alignItems: "center", gap: "8px",
    fontSize: "12px", color: "#555",
  },
  slider: { width: "160px", cursor: "pointer" },
  vizContainer: {
    position: "relative", display: "block",
    width: WIDTH + "px", height: HEIGHT + "px", lineHeight: 0,
  },
  canvas: { position: "absolute", top: 0, left: 0, display: "block" },
  svg:    { position: "absolute", top: 0, left: 0, background: "transparent", overflow: "visible" },
  info:   { fontSize: "12px", color: "#555", minHeight: "18px", textAlign: "center" },
};


function buildRegions(labels, matrix, threshold, mode) {
  const n = labels.length;
  return labels.map((label, i) => {
    const imports = [];
    for (let j = 0; j < n; j++) {
      if (i === j) continue;
      const val = matrix[i][j];
      if (val === 0) continue;
      if (mode === "tracts" && (val < threshold[0] || val > threshold[1])) continue;
      imports.push(labels[j]);
    }
    return { name: label, imports };
  });
}



function bilink(root) {
  const map = new Map(root.leaves().map(d => [d.data.name, d]));
  for (const d of root.leaves()) { d.incoming = []; d.outgoing = []; }
  for (const d of root.leaves()) {
    for (const name of d.data.imports) {
      const target = map.get(name);
      if (target) {
        d.outgoing.push([d, target]);
        target.incoming.push([d, target]);
      }
    }
  }
  return root;
}


function drawEdge(ctx, src, tgt, color, lineGen) {
  const d = lineGen(src.path(tgt));
  if (!d) return;
  ctx.strokeStyle = color;
  ctx.stroke(new Path2D(d));
}

function renderEdges(canvas, root, selectedName, lineGen) {
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, WIDTH, HEIGHT);
  ctx.save();
  ctx.translate(CX, CY);

  const edges        = root.leaves().flatMap(leaf => leaf.outgoing);
  const hasSelection = selectedName !== null;

  if (hasSelection) {
    ctx.lineWidth = 0.8;
    for (const [s, t] of edges)
      if (s.data.name !== selectedName && t.data.name !== selectedName)
        drawEdge(ctx, s, t, COLOR_DIM, lineGen);
    ctx.lineWidth = 1.8;
    for (const [s, t] of edges) {
      if      (s.data.name === selectedName) drawEdge(ctx, s, t, COLOR_OUTGOING, lineGen);
      else if (t.data.name === selectedName) drawEdge(ctx, s, t, COLOR_INCOMING, lineGen);
    }
  } else {
    ctx.lineWidth = 0.9;
    for (const [s, t] of edges) drawEdge(ctx, s, t, COLOR_DEFAULT, lineGen);
  }

  ctx.restore();
}



function getTractRange(labels, matrix) {
  const n = labels.length;
  let min = Infinity, max = -Infinity;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      if (i !== j && matrix[i][j] !== 0) {
        min = Math.min(min, matrix[i][j]);
        max = Math.max(max, matrix[i][j]);
      }
    }
  }
  return [Math.floor(min), Math.ceil(max)];
}



export default function Connectivity({ connectivity }) {
  const canvasRef                       = React.useRef(null);
  const [mode, setMode]                 = React.useState("weights");
  const [selectedName, setSelectedName] = React.useState(null);
  const [infoText, setInfoText]         = React.useState("Click a region to highlight its connections.");


  const tractRange   = React.useMemo(() => {
    return getTractRange(connectivity.region_labels, connectivity.tract_lengths);
  }, [connectivity]);

  const [tractMin, setTractMin] = React.useState(null);
  const [tractMax, setTractMax] = React.useState(null);


  React.useEffect(() => {
    setTractMin(tractRange[0]);
    setTractMax(tractRange[1]);
  }, [tractRange]);

  const threshold = [tractMin ?? tractRange[0], tractMax ?? tractRange[1]];

  const { root, lineGen } = React.useMemo(() => {
    const matrix  = mode === "weights" ? connectivity.weights : connectivity.tract_lengths;
    const regions = buildRegions(connectivity.region_labels, matrix, threshold, mode);
    const root    = cluster().size([2 * Math.PI, RADIUS])(
      bilink(
        hierarchy({ name: "root", children: regions })
          .sort((a, b) => a.height - b.height)
      )
    );
    const lineGen = lineRadial()
      .curve(curveBundle.beta(0.95))
      .radius(d => d.y)
      .angle(d => d.x);
    return { root, lineGen };
  }, [connectivity, mode, tractMin, tractMax]);

  React.useEffect(() => {
    if (canvasRef.current) renderEdges(canvasRef.current, root, selectedName, lineGen);
  }, [root, selectedName, lineGen]);

  React.useEffect(() => {
    setSelectedName(null);
    setInfoText("Click a region to highlight its connections.");
  }, [mode]);

  const handleNodeClick = React.useCallback((name) => {
    setSelectedName(prev => {
      if (prev === name) {
        setInfoText("Click a region to highlight its connections.");
        return null;
      }
      const leaf = root.leaves().find(l => l.data.name === name);
      setInfoText(`${name} — ${leaf?.outgoing?.length ?? 0} outgoing (red), ${leaf?.incoming?.length ?? 0} incoming (green)`);
      return name;
    });
  }, [root]);

  const svgLabels = React.useMemo(() => {
    const leaves       = root.leaves();
    const selectedLeaf = selectedName ? leaves.find(l => l.data.name === selectedName) : null;
    const outSet       = new Set(selectedLeaf?.outgoing?.map(([, t]) => t.data.name) ?? []);
    const inSet        = new Set(selectedLeaf?.incoming?.map(([s])   => s.data.name) ?? []);

    return leaves.map(leaf => {
      const name       = leaf.data.name;
      const isSelected = name === selectedName;
      const isOut      = outSet.has(name);
      const isIn       = inSet.has(name);

      const nx      = leaf.y * Math.cos(leaf.x - Math.PI / 2);
      const ny      = leaf.y * Math.sin(leaf.x - Math.PI / 2);
      const lx      = (leaf.y + 16) * Math.cos(leaf.x - Math.PI / 2);
      const ly      = (leaf.y + 16) * Math.sin(leaf.x - Math.PI / 2);
      const deg     = leaf.x * 180 / Math.PI - 90;
      const isRight = leaf.x < Math.PI;
      const anchor  = isRight ? "start" : "end";
      const rotate  = isRight ? deg : deg + 180;

      let fill = "#444";
      if (isSelected)        fill = "#f39c12";
      else if (isOut)        fill = "#e74c3c";
      else if (isIn)         fill = "#27ae60";
      else if (selectedName) fill = "#bbb";

      return (
        <g key={name} onClick={() => handleNodeClick(name)} style={{ cursor: "pointer" }}>
          <circle cx={nx} cy={ny} r={isSelected ? 5 : 3.5}
            fill={isSelected ? COLOR_NODE_SELECTED : COLOR_NODE_DEFAULT} />
          <text
            transform={`translate(${lx},${ly}) rotate(${rotate})`}
            textAnchor={anchor} dominantBaseline="middle"
            fontSize={isSelected ? 12 : 10}
            fontWeight={isSelected || isOut || isIn ? "bold" : "normal"}
            fill={fill}
          >{name}</text>
        </g>
      );
    });
  }, [root, selectedName, handleNodeClick]);

  return (
    <div style={STYLES.root}>
      <div style={STYLES.controls}>
        {/* Mode toggle */}
        <button
          style={mode === "weights" ? {...STYLES.btnBase, ...STYLES.btnActive} : STYLES.btnBase}
          onClick={() => setMode("weights")}>Weights</button>
        <button
          style={mode === "tracts" ? {...STYLES.btnBase, ...STYLES.btnActive} : STYLES.btnBase}
          onClick={() => setMode("tracts")}>Tract Lengths</button>
        {selectedName && (
          <button style={STYLES.btnClear} onClick={() => handleNodeClick(selectedName)}>
            ✕ Clear</button>
        )}
      </div>

      {/* Tract length range sliders — only shown in tracts mode */}
      {mode === "tracts" && (
        <div style={STYLES.controls}>
          <div style={STYLES.sliderRow}>
            <span>Min tract:</span>
            <input type="range" style={STYLES.slider}
              min={tractRange[0]} max={tractRange[1]} step={1}
              value={tractMin ?? tractRange[0]}
              onChange={e => {
                const v = Number(e.target.value);
                setTractMin(v);
                if (v > tractMax) setTractMax(v);
              }} />
            <span style={{ minWidth: "40px" }}>{tractMin ?? tractRange[0]} mm</span>
          </div>
          <div style={STYLES.sliderRow}>
            <span>Max tract:</span>
            <input type="range" style={STYLES.slider}
              min={tractRange[0]} max={tractRange[1]} step={1}
              value={tractMax ?? tractRange[1]}
              onChange={e => {
                const v = Number(e.target.value);
                setTractMax(v);
                if (v < tractMin) setTractMin(v);
              }} />
            <span style={{ minWidth: "40px" }}>{tractMax ?? tractRange[1]} mm</span>
          </div>
        </div>
      )}

      <div style={STYLES.vizContainer}>
        <canvas ref={canvasRef} width={WIDTH} height={HEIGHT} style={STYLES.canvas} />
        <svg width={WIDTH} height={HEIGHT}
             viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
             style={STYLES.svg}>
          <g transform={`translate(${CX},${CY})`}>
            {svgLabels}
          </g>
        </svg>
      </div>

      <div style={STYLES.info}>{infoText}</div>
    </div>
  );
}