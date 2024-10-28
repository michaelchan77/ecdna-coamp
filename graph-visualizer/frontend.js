// document.addEventListener('DOMContentLoaded', function () {
//     cytoscape.use(cytoscapePopper(tippyFactory));
// });

async function loadGraph() {
    cytoscape.use(cytoscapePopper(tippyFactory));

    // input gene
    const inputNode = $('#textBox').val().trim().toUpperCase();

    // filters
    const minWeight = parseFloat($('#edgeWeight').val());
    const sampleMinimum = parseFloat($('#numSamples').val());
    const oncogenesChecked = $('#oncogenes_only').is(':checked');
    const allEdgesChecked = $('#all_edges').is(':checked');
    // print vars
    document.getElementById('storedText').textContent = String([minWeight, sampleMinimum, oncogenesChecked, allEdgesChecked]);
    
    // alert
    if (!inputNode) {
        alert("Please enter a gene name.");
        return;
    }

    // Clear any existing graph
    document.getElementById('cy').innerHTML = '';

    // Fetch the subgraph data from your Flask server
    try {
        const response = await fetch(`http://127.0.0.1:5000/getNodeData?name=${inputNode}&min_weight=${minWeight}&min_samples=${sampleMinimum}&oncogenes=${oncogenesChecked}&all_edges=${allEdgesChecked}`);
        if (!response.ok) {
            throw new Error(`Node ${inputNode} not found or server error.`);
        }

        const data = await response.json();

        // Initialize Cytoscape with fetched data
        const cy = cytoscape({
            container: document.getElementById('cy'),
            elements: data,  // Use the data from the server
            style: [
                { selector: 'node', style: { 'background-color': '#A7C6ED', 'label': 'data(name)' } },
                { selector: `node[oncogene="True"]`, style: { 'background-color': '#A7C6ED', 'label': 'data(name)', 'border-width': 2, 'border-color': 'black', 'border-style': 'solid' } },
                { selector: `node[name="${inputNode}"]`, style: { 'background-color': '#e04347', 'label': 'data(name)' } },
                { selector: 'edge', style: { 'width': 2, 'line-color': '#ccc' } }
            ],
            layout: { name: 'fcose' }
        });

        // Update sample slider max
        updateSampleMax(cy);

        // Make test tip for input node
        var a = cy.nodes(`[label == ${inputNode}]`);
        var makeContent = function(text) {
            var div = document.createElement('div');
            div.innerHTML = text;
            return div;
        };
        var tippyA = a.popper({
            content: makeContent('foo'),
        });
        tippyA.show();

        // cy.nodes().forEach(node => {

        // });

        // // Store reference to current subset
        // let currentSubset = cy

        // document.getElementById('edgeWeight').addEventListener('change', updateVisibleElements);
        // document.getElementById('numSamples').addEventListener('change', updateVisibleElements);

        // // Function to update visible elements based on sliders
        // function updateVisibleElements() {
        //     if (currentSubset.length === 0) return; // Do nothing if no subset is selected

        //     let sliderValue = parseFloat($('#edgeWeight').val());
        //     let sampleVal = parseInt($('#numSamples').val());

        //     // Show all edges within subset
        //     currentSubset.show();

        //     // Hide edges with weight < slider value
        //     currentSubset.edges().forEach(edge => {
        //         const weight = edge.data('weight');
        //         const numSamples = edge.data('total_samples');

        //         if (weight < sliderValue || numSamples < sampleVal) {
        //             edge.hide();
        //             edge.connectedNodes().hide(); // Hide connected nodes
        //         }
        //     });

        //     // Fit the viewport to the remaining visible elements
        //     cy.fit(currentSubset);
        // }

        // // Checkbox handler for oncogenes
        // let nonOncogenesSubset = null;

        // document.getElementById('oncogenes_only').addEventListener('change', toggleOncogenes);

        // function toggleOncogenes(event) {
        //     const isChecked = event.target.checked;

        //     if (isChecked) {
        //         currentSubset.nodes().forEach(node => {
        //             const oncogene_status = node.data('oncogene_status');
    
        //             if (!oncogene_status) {
        //                 node.hide();
        //                 node.connectEdges().hide(); // Hide connected nodes
        //             }
        //         });
        //         cy.fit(currentSubset);
        //     }
        //     else {
        //         currentSubset.fit();
        //     }
        // }

    } catch (error) {
        alert(error.message);
    }
}

function updateSampleMax(cy) {
    if (cy) {
        maxSamples = 1;
        cy.edges().forEach(edge => {
            const samples = edge.data('lenunion');
            if (samples > maxSamples) {
                maxSamples = samples;
            }
        });
        document.getElementById('numSamples').max = maxSamples;
        document.getElementById('sampleMaxText').textContent = maxSamples;
    }
}

// https://github.com/cytoscape/cytoscape.js-popper/blob/master/demo-tippy.html
function tippyFactory(ref, content){
    // Since tippy constructor requires DOM element/elements, create a placeholder
    var dummyDomEle = document.createElement('div');

    var tip = tippy( dummyDomEle, {
        getReferenceClientRect: ref.getBoundingClientRect,
        trigger: 'manual', // mandatory
        // dom element inside the tippy:
        content: content,
        // your own preferences:
        arrow: true,
        placement: 'bottom',
        hideOnClick: false,
        sticky: "reference",

        // if interactive:
        interactive: true,
        appendTo: document.body // or append dummyDomEle to document.body
    } );

    return tip;
}
