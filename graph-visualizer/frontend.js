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
        console.log(data)
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


        // Initialize Gene Data Column with fetched data
        const datacontainer = document.getElementById('data-container');
        datacontainer.innerHTML = ''; // Clear previous rows

        cy.nodes().forEach(node => {
            row = document.createElement('tr');
    
            const cellName = document.createElement('td');
            const geneName = node.data('name'); // Get the gene name
            const link = document.createElement('a');
            
            // Set the href attribute to the desired URL (customize this URL as needed)
            link.href = `https://depmap.org/portal/gene/${geneName}?tab=overview`; // Replace with your actual URL
            link.textContent = geneName; // Set the text to the gene name
            link.target = '_blank'; // Open the link in a new tab (optional)

            cellName.appendChild(link);
    
            cellStatus = document.createElement('td');
            cellStatus.textContent = node.data('oncogene'); // Adjust based on your data structure
    
            row.appendChild(cellName);
            row.appendChild(cellStatus);
            datacontainer.appendChild(row);
        });

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
