document.addEventListener('DOMContentLoaded', function () {
    cytoscape.use(cytoscapePopper(tippyFactory));
});

async function loadGraph() {
    const inputNode = $('#textBox').val().trim().toUpperCase();

    if (!inputNode) {
        alert("Please enter a gene name.");
        return;
    }

    // Clear any existing graph
    document.getElementById('cy').innerHTML = '';

    // Fetch the subgraph data from your Flask server
    try {
        const response = await fetch(`http://127.0.0.1:5000/getNodeData?name=${inputNode}`);
        if (!response.ok) {
            throw new Error(`Node ${inputNode} not found or server error.`);
        }

        const data = await response.json();

        // Initialize Cytoscape with fetched data
        const cy = cytoscape({
            container: document.getElementById('cy'),
            elements: data,  // Use the data from the server
            style: [
                { selector: 'node', style: { 'background-color': '#666', 'label': 'data(name)' } },
                { selector: 'edge', style: { 'width': 2, 'line-color': '#ccc' } }
            ],
            layout: { name: 'fcose' }
        });

        // Store reference to current subset
        let currentSubset = cy.collection(data);

        // Function to update visible elements based on sliders
        function updateVisibleElements() {
            if (currentSubset.length === 0) return; // Do nothing if no subset is selected

            let sliderValue = parseFloat($('#edgeWeight').val());
            let sampleVal = parseInt($('#numSamples').val());

            // Show all edges within subset
            currentSubset.show();

            // Hide edges with weight < slider value
            currentSubset.edges().forEach(edge => {
                const weight = edge.data('weight') || 0;
                const numSamples = edge.data('total_samples') || 0;

                if (weight < sliderValue || numSamples < sampleVal) {
                    edge.hide();
                    edge.connectedNodes().hide(); // Hide connected nodes
                }
            });

            // Fit the viewport to the remaining visible elements
            cy.fit(currentSubset);
        }

        // Slider handlers
        $('#edgeWeight').on('input', updateVisibleElements);
        $('#numSamples').on('input', updateVisibleElements);

        // Checkbox handler for oncogenes
        let nonOncogenesSubset = null;

        document.getElementById('oncogenes_only').addEventListener('change', toggleOncogenes);

        function toggleOncogenes() {
            const isChecked = this.checked;

            if (isChecked) {
                // Remove non-oncogenes from the graph
                nonOncogenesSubset = cy.elements('node[!oncogene_status]');
                cy.remove(nonOncogenesSubset);
            } else {
                // Add back non-oncogenes
                if (nonOncogenesSubset) {
                    cy.add(nonOncogenesSubset);
                    nonOncogenesSubset = null;
                }
            }
        }

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
