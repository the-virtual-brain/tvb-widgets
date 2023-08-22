import * as React from "react";
import * as d3 from "d3";


/**
 * This separator should be present in the labels of nodes only when we want hierarchical nodes.
 * Currently this is not used, but will be useful for macro-regions.
 * When found in original names, will be replaced with HIERARCHY_SEPARATOR_REPLACEMENT.
 */
const HIERARCHY_SEPARATOR = ".";
const HIERARCHY_SEPARATOR_REPLACEMENT = "_";
const colorin = "#00f";
const colorout = "#f00";
const colornone = "#ccc";

/**
 * A function for drawing a hierarchical edge bundle
 *
 * @param data    The data structure that has the region labels and the adjiacence matrix
 * @param testFn  Callable for filtering edges
 */
export function initHierarchicalEdgeBundle(data, testFn) {

    const l = data.region_labels.length;
    // let svgD3 = data.svg.d3;
    let jsonified_region_labels = [];
    let hasSpecialCharacters = false;

    for (let i = 0; i < l; i++) {
        let json_line = {
            imports: undefined,
            name: undefined,
            // children: []
        };
        json_line.imports = [];
        // json_line.children = [];
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
    console.log('json:  ', jsonified_region_labels);
    return jsonified_region_labels;
}

function hierarchy(data, delimiter = HIERARCHY_SEPARATOR) {
    console.log('data inside hierarchy: ', data);
    let root;
    const map = new Map;
    let newData = []
    data.forEach(function find(d) {
        const {name} = d;
        if (map.has(name)) {
            return map.get(name);
        }
        const i = name.lastIndexOf(delimiter);
        map.set(name, d);
        if (node) {
            find({name: name.substring(0, i), children: []}).children.push(d);
            d.name = name.substring(i + 1);
        } else {
            root = d;
        }
        newData.push(root);
    });
    console.log('data after hierarchy: ', data);
    console.log('map after hierarchy: ', map);
    console.log('newData after hierarchy: ', newData);
    return newData;
}

function bilink(root) {
    console.log('before map');
    const map = new Map(root.leaves().map(d => [id(d), d]));
    console.log('after map');
    for (const d of root.leaves()) {
        d.incoming = [];
        const imports = d.data.imports;
        d.outgoing = imports ? imports.map(i => [d, map.get(i)]) : [];
    }
    for (const d of root.leaves()) for (const o of d.outgoing) o[1].incoming.push(o);
    return root;
}

function id(node) {
    return `${node.parent ? id(node.parent) + "." : ""}${node.data.name}`;
}

const BUNDLE = {
    tracts: "tracts",
    weights: "weights"
};

export default function Connectivity({connectivity, on_connectivity}) {
    const ref = React.useRef();
    const [bundle, setBundle] = React.useState(BUNDLE.weights);

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
    let chart = () => {
    };
    React.useEffect(() => {
        // const svg = d3.select("#middle-edge-bundle");

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
        // const data = hierarchy(dataJson);
        const data = dataJson;

        console.log("data=hierarchy(dataJson):: ", data);

        // connectivityEdgesData.matrix = [2, 0, 1, 0];
        chart = () => {
            const width = 954;
            const radius = width / 2;

            const tree = d3.cluster()
                .size([2 * Math.PI, radius - 100]);
            const root = tree(bilink(d3.hierarchy(data, d => d && d.children || [])
                .sort((a, b) => d3.ascending(a.height, b.height) || d3.ascending(a.data.name, b.data.name))));

            const svg = d3.create("svg")
                .attr("width", width)
                .attr("height", width)
                .attr("viewBox", [-width / 2, -width / 2, width, width])
                .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");
            // ref.current && ref.current.appendChild(svg.node());

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
                d3.selectAll(d.incoming.map(d => d.path)).attr("stroke", colorin).raise();
                d3.selectAll(d.incoming.map(([d]) => d.text)).attr("fill", colorin).attr("font-weight", "bold");
                d3.selectAll(d.outgoing.map(d => d.path)).attr("stroke", colorout).raise();
                d3.selectAll(d.outgoing.map(([, d]) => d.text)).attr("fill", colorout).attr("font-weight", "bold");
            }

            function outed(event, d) {
                link.style("mix-blend-mode", "multiply");
                d3.select(this).attr("font-weight", null);
                d3.selectAll(d.incoming.map(d => d.path)).attr("stroke", null);
                d3.selectAll(d.incoming.map(([d]) => d.text)).attr("fill", null).attr("font-weight", null);
                d3.selectAll(d.outgoing.map(d => d.path)).attr("stroke", null);
                d3.selectAll(d.outgoing.map(([, d]) => d.text)).attr("fill", null).attr("font-weight", null);
            }

            // return svg.node();
            ref.current && ref.current.appendChild(svg.node());
        }

        console.log('chart: ', chart());

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
        <div ref={ref}
        ></div>
    </div>)
}
