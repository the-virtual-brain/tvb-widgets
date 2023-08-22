import * as React from "react";
// import * as d3 from "d3@4.10.0";
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

    const regionLabelsLength = data.region_labels.length;
    let svgD3 = data.svg.d3;
    let jsonified_region_labels = [];
    let hasSpecialCharacters = false;

    for (let i = 0; i < regionLabelsLength; i++) {
        let json_line = {
            imports: undefined,
            name: undefined
        };
        json_line.imports = [];
        let k = 0; //k is a counter for connected regions with the j-th region
        for (let j = 0; j < regionLabelsLength; j++) {
            let w = 0;
            w = data.matrix && data.matrix[i * regionLabelsLength + j];
            hasSpecialCharacters = hasSpecialCharacters || (data.region_labels[i].lastIndexOf(HIERARCHY_SEPARATOR) > 0);
            json_line.name = data.region_labels[i].replace(HIERARCHY_SEPARATOR, HIERARCHY_SEPARATOR_REPLACEMENT);
            if (testFn(w)) {
                json_line.imports[k] = data.region_labels[j].replace(HIERARCHY_SEPARATOR, HIERARCHY_SEPARATOR_REPLACEMENT);
                k++;
            }
        }
        jsonified_region_labels[i] = json_line;
    }

    console.log('jsonified: ', jsonified_region_labels);
    if (hasSpecialCharacters) {
        console.log("Special character '" + HIERARCHY_SEPARATOR + "' has been replaced in all labels with '" + HIERARCHY_SEPARATOR_REPLACEMENT);
    }

    console.log('data: ', data);
    let radius = data.svg.svg.getAttribute("height") / 2;
    console.log('radius: ', radius);
    let innerRadius = radius - 100; // substract estimated labels size

    const cluster = d3.cluster()
        .size([360, innerRadius]);

    let line = d3.radialLine()
        .curve(d3.curveBundle.beta(0.85))
        .radius(function (d) {
            return d.y;
        })
        .angle(function (d) {
            return d.x / 180 * Math.PI;
        });

    const svg = svgD3
        .append("g")
        .attr("transform", "translate(" + radius + "," + radius + ")");

    let link = svg.append("g").selectAll(".link"),
        node = svg.append("g").selectAll(".node");
    console.log('before packageHierarchy');
    const root = packageHierarchy(jsonified_region_labels)
        .sum(function (d) {
            return d.size;
        });
    console.log('before packageHierarchy');
    cluster(root);
    console.log('root: ', root);
    console.log('after cluster');

    link = link
        .data(packageImports(root.leaves()))
        .enter().append("path")
        .each(function (d) {
            d.source = d[0];
            d.target = d[d.length - 1];
        })
        .attr("class", "link")
        .attr("d", line);

    console.log('after link');

    node = node
        .data(root.leaves())
        .enter().append("text")
        .attr("class", "node")
        .attr("dy", "0.31em")
        .attr("transform", function (d) {
            return "rotate(" + (d.x - 90) + ")translate(" + (d.y + 8) + ",0)" + (d.x < 180 ? "" : "rotate(180)");
        })
        .attr("text-anchor", function (d) {
            return d.x < 180 ? "start" : "end";
        })
        .text(function (d) {
            return d.data.key;
        })
        .on("mouseover", mouseovered)
        .on("mouseout", mouseouted);

    console.log('after node');

    function mouseovered(d) {
        node
            .each(function (n) {
                n.target = n.source = false;
            });

        link
            .classed("link-target", function (l) {
                if (l.target === d) return l.source.source = true;
            })
            .classed("link-source", function (l) {
                if (l.source === d) return l.target.target = true;
            })
            .filter(function (l) {
                return l.target === d || l.source === d;
            })
            .raise();

        node
            .classed("node-target", function (n) {
                return n.target;
            })
            .classed("node-source", function (n) {
                return n.source;
            });
    }

    function mouseouted(d) {
        link
            .classed("link-target", false)
            .classed("link-source", false);

        node
            .classed("node-target", false)
            .classed("node-source", false);
    }

// Lazily construct the package hierarchy from class names.
    function packageHierarchy(classes) {
        var map = {};

        function find(name, data) {
            var node = map[name], i;
            if (!node) {
                node = map[name] = data || {name: name, children: []};
                if (name.length) {
                    node.parent = find(name.substring(0, i = name.lastIndexOf(HIERARCHY_SEPARATOR)), data);
                    console.log('node.parent: ', node.parent);
                    if (node.parent.children) node.parent.children.push(node);
                    node.key = name.substring(i + 1);
                }
            }
            return node;
        }

        classes.forEach(function (d) {
            find(d.name, d);
        });

        return d3.hierarchy(map[""]);
    }

//     function packageHierarchy(data, delimiter = ".") {
//         let root;
//         const map = new Map;
//         data.forEach(function find(data) {
//             const {name} = data;
//             if (map.has(name)) return map.get(name);
//             const i = name.lastIndexOf(delimiter);
//             map.set(name, data);
//             if (i >= 0) {
//                 find({name: name.substring(0, i), children: []}).children.push(data);
//                 data.name = name.substring(i + 1);
//             } else {
//                 root = data;
//             }
//             return data;
//         });
//         return root;
//     }

// Return a list of imports for the given array of nodes.
    function packageImports(nodes) {
        console.log('inside package imports');
        const map = {};
        const imports = [];

        console.log('before foreach 1');
        // Compute a map from name to node.
        nodes.forEach(function (d) {
            map[d.data.name] = d;
        });

        console.log('after foreach 1');


        // For each import, construct a link from the source to target node.
        nodes.forEach(function (d) {
            d.data.imports &&
            d.data.imports.forEach(function (i) {
                console.log('d.data.imports.forEach(function (i) -> i: ', i);
                console.log('d.data.imports.forEach(function (i) -> map[i]: ', map[i]);
                console.log('d.data.imports.forEach(function (i) -> map[d.data.name]: ', map[d.data.name]);
                map[i] && imports.push(map[d.data.name].path(map[i]));
            });
        });
        console.log('before return with vallue: ', imports);
        return imports;
    }


}

const BUNDLE = {
    tracts: "tracts",
    weights: "weights"
};

export default function Connectivity({connectivity, on_connectivity}) {
    const ref = React.useRef();
    console.log('reeeeeeeeeeeef: ', ref.current);
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

    React.useEffect(() => {
        const svg = d3.select("#middle-edge-bundle");

        connectivityEdgesData.region_labels = connectivity.region_labels;
        connectivityEdgesData.svg.d3 = svg;
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
        // connectivityEdgesData.matrix = [2, 0, 1, 0];
        connectivityEdgesData.svg.d3.selectAll("*")
            .transition()
            .duration(100)
            .style("fill-opacity", "0");
        console.log('connectivityEdgesData: ', connectivityEdgesData);
        connectivityEdgesData.svg.d3.selectAll("*").remove();
        connectivityEdgesData.state = bundle;
        initHierarchicalEdgeBundle(connectivityEdgesData, d => d !== 0);

        connectivityEdgesData.svg.d3.selectAll("*")
            .transition()
            .duration(100)
            .style("fill-opacity", "1");

        // return () => {
        //     svg.remove();
        // };
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
        <svg ref={ref}
             height={"700"}
             width={"700"}
             viewBox="0 0 700 700"
             preserveAspectRatio="xMidYMax meet"
             className="diagram-svg"
             id="middle-edge-bundle"></svg>
    </div>)
}
