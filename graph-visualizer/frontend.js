document.addEventListener('DOMContentLoaded', function () {
    cytoscape.use(cytoscapePopper(tippyFactory));
});

async function loadGraph() {
    // input gene
    const inputNode = $('#textBox').val().trim().toUpperCase();
    
    // filters
    const minWeight = parseFloat($('#edgeWeight').val());
    const sampleMinimum = parseFloat($('#numSamples').val());
    const oncogenesChecked = $('#oncogenes_only').is(':checked');
    const allEdgesChecked = $('#all_edges').is(':checked');
    
    document.getElementById('storedText').textContent = String([minWeight, sampleMinimum, oncogenesChecked, allEdgesChecked]);

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
                { selector: 'node', style: { 'background-color': '#666', 'label': 'data(name)' } },
                { selector: 'edge', style: { 'width': 2, 'line-color': '#ccc' } }
            ],
            layout: { name: 'fcose' }
        });

        cy.nodes().forEach(node => {
            
        });

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
