import * as React from "react";
import * as d3 from "d3";


/**
 * This separator should be present in the labels of nodes only when we want hierarchical nodes.
 * Currently this is not used, but will be useful for macro-regions.
 * When found in original names, will be replaced with HIERARCHY_SEPARATOR_REPLACEMENT.
 */
const HIERARCHY_SEPARATOR = ".";
const HIERARCHY_SEPARATOR_REPLACEMENT = "_";

/**
 * A function for drawing a hierarchical edge bundle
 *
 * @param data    The data structure that has the region labels and the adjiacence matrix
 * @param testFn  Callable for filtering edges
 */
export function initHierarchicalEdgeBundle(data, testFn) {

    const l = data.region_labels.length;
    let jsonified_region_labels = [];
    let hasSpecialCharacters = false;

    for (let i = 0; i < l; i++) {
        let json_line = {
            imports: undefined,
            name: undefined,
        };
        json_line.imports = [];
        let k = 0; //k is a counter for connected regions with the j-th region
        for (let j = 0; j < l; j++) {
            let w = 0;
            w = data.matrix[i * l + j];
            hasSpecialCharacters = hasSpecialCharacters || (data.region_labels[i].lastIndexOf(HIERARCHY_SEPARATOR) > 0);
            json_line.name = data.region_labels[i].replace(HIERARCHY_SEPARATOR, HIERARCHY_SEPARATOR_REPLACEMENT);
            if (testFn(w)) {
                json_line.imports[k] = data.region_labels[j].replace(HIERARCHY_SEPARATOR, HIERARCHY_SEPARATOR_REPLACEMENT);
                k++;
            }
        }
        jsonified_region_labels[i] = json_line;
    }
    return jsonified_region_labels;
}

const BUNDLE = {
    tracts: "tracts",
    weights: "weights"
};

export default function Connectivity({connectivity, on_connectivity}) {
    const ref = React.useRef();
    const [bundle, setBundle] = React.useState(BUNDLE.weights);

    const colorin = "#00f";
    const colorout = "#f00";
    const colornone = "#ccc";

    const connectivityEdgesData = {
        region_labels: [""],
        matrix: [],
        svg: {
            d3: null,
            svg: null,
        },
        data_url: "",
        state: bundle
    };

    React.useEffect(() => {
        connectivityEdgesData.region_labels = connectivity.region_labels;
        connectivityEdgesData.svg.d3 = d3.select("#middle-edge-bundle");
        connectivityEdgesData.svg.svg = document.querySelector("#middle-edge-bundle");
        let tracts1D = [];
        let weights1D = [];
        for (const subArr of connectivity.tract_lengths) {
            tracts1D = tracts1D.concat(subArr);
        }
        for (const subArr of connectivity.weights) {
            weights1D = weights1D.concat(subArr);
        }
        console.log(connectivityEdgesData.region_labels);
        connectivityEdgesData.matrix = bundle === BUNDLE.weights ? weights1D : tracts1D;
        const dataJson = initHierarchicalEdgeBundle(connectivityEdgesData, d => d !== 0);
        const data = {name: 'root', children: dataJson};

        function id(node) {
            return node.data.name;
        }

        function hierarchy(data, delimiter = ".") {
            let root;
            const map = new Map;
            data.forEach(function find(data) {
                const {name} = data;
                if (map.has(name)) return map.get(name);
                const i = name.lastIndexOf(delimiter);
                map.set(name, data);
                if (i >= 0) {
                    find({name: name.substring(0, i), children: []}).children.push(data);
                    data.name = name.substring(i + 1);
                } else {
                    root = data;
                }
                return data;
            });
            return root;
        }

        function bilink(root) {
            const map = new Map(root.leaves().map(d => [id(d), d]));
            for (const d of root.leaves()) {
                d.incoming = [];
                d.outgoing = [];

                for (const i of d.data.imports) {
                    const target = map.get(i);
                    if (target) {
                        d.outgoing.push([d, target]);
                        if (!target.incoming) target.incoming = [];
                        target.incoming.push([d, target]);
                    }
                }
            }
            return root;
        }

        // Visualization code
        const width = 954;
        const radius = width / 2;

        const tree = d3.cluster()
            .size([2 * Math.PI, radius - 100]);
        const root = tree(bilink(d3.hierarchy(data)
            .sort((a, b) => d3.ascending(a.height, b.height) || d3.ascending(a.data.name, b.data.name))));
        console.log('root: ', root);
        const svg = d3.create("svg")
            .attr("width", width)
            .attr("height", width)
            .attr("viewBox", [-width / 2, -width / 2, width, width])
            .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

        const node = svg.append("g")
            .selectAll()
            .data(root.leaves())
            .join("g")
            .attr("transform", d => `rotate(${d.x * 180 / Math.PI - 90}) translate(${d.y},0)`)
            .append("text")
            .attr("dy", "0.31em")
            .attr("x", d => d.x < Math.PI ? 6 : -6)
            .attr("text-anchor", d => d.x < Math.PI ? "start" : "end")
            .attr("transform", d => d.x >= Math.PI ? "rotate(180)" : null)
            .text(d => d.data.name)
            .each(function (d) {
                d.text = this;
            })
            .on("mouseover", overed)
            .on("mouseout", outed)
            .call(text => text.append("title").text(d => `${id(d)}
  ${d.outgoing.length} outgoing
  ${d.incoming.length} incoming`));

        const line = d3.lineRadial()
            .curve(d3.curveBundle.beta(0.85))
            .radius(d => d.y)
            .angle(d => d.x);

        const link = svg.append("g")
            .attr("stroke", colornone)
            .attr("fill", "none")
            .selectAll()
            .data(root.leaves().flatMap(leaf => leaf.outgoing))
            .join("path")
            .style("mix-blend-mode", "multiply")
            .attr("d", ([i, o]) => line(i.path(o)))
            .each(function (d) {
                d.path = this;
            });

        function overed(event, d) {
            link.style("mix-blend-mode", null);
            d3.select(this).attr("font-weight", "bold");

            // Highlight incoming lines and text
            d3.selectAll(d.incoming.map(d => d.path)).attr("stroke", colorin).raise();
            d3.selectAll(d.incoming.map(([d]) => d.text)).attr("fill", colorin).attr("font-weight", "bold");

            // Highlight outgoing lines and text
            d3.selectAll(d.outgoing.map(d => d.path)).attr("stroke", colorout).raise();
            d3.selectAll(d.outgoing.map(([, d]) => d.text)).attr("fill", colorout).attr("font-weight", "bold");
        }

        function outed(event, d) {
            link.style("mix-blend-mode", "multiply");
            d3.select(this).attr("font-weight", null);

            // Reset styles for incoming lines and text
            d3.selectAll(d.incoming.map(d => d.path)).attr("stroke", null);
            d3.selectAll(d.incoming.map(([d]) => d.text)).attr("fill", null).attr("font-weight", null);

            // Reset styles for outgoing lines and text
            d3.selectAll(d.outgoing.map(d => d.path)).attr("stroke", null);
            d3.selectAll(d.outgoing.map(([, d]) => d.text)).attr("fill", null).attr("font-weight", null);
        }

        // Append the SVG to the visualization container
        ref.current?.appendChild(svg.node());

        return () => svg.remove();

        // chart();
    }, [connectivity, bundle]);

    return (<div>
        <aside>
            <select onChange={(e) => {
                setBundle(e.target.value)
            }}>
                <option value={"tracts"} selected={bundle === BUNDLE.tracts}>Tracts</option>
                <option value={"weights"} selected={bundle === BUNDLE.weights}>Weights</option>
            </select>
        </aside>
        <div ref={ref} id={"visualization"}
        ></div>
    </div>)
}
