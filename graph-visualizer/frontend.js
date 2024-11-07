function tippyFactory(ref, content, theme){
    // Since tippy constructor requires DOM element/elements, create a placeholder
    var dummyDomEle = document.createElement('div');
 
    var tip = tippy( dummyDomEle, {
        getReferenceClientRect: ref.getBoundingClientRect,
        trigger: 'manual', // mandatory
        // dom element inside the tippy:
        content: content,
        // preferences:
        arrow: false,
        placement: 'bottom-end',
        hideOnClick: false,
        sticky: "reference",
        theme: theme,
        allowHTML: true,
 
        // if interactive:
        interactive: true,
        appendTo: document.body
    } );
 
    return tip;
 }

document.addEventListener('DOMContentLoaded', function () {
    cytoscape.use( cytoscapePopper(tippyFactory) );
});

async function loadGraph() {
    console.log("Load graph pressed");

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

    // Fetch the subgraph data from Flask server
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
                { selector: 'node', style: { 'background-color': '#A7C6ED', 'label': '' } },
                { selector: `node[name="${inputNode}"], node.highlighted`, style: {'z-index': 100, 'label': 'data(name)' } }, //, 'border-width': 2, 'border-color': 'black', 'border-style': 'solid' } },
                { selector: `node[oncogene="True"]`, style: { 'background-color': '#ff4757', 'z-index': 10, 'label': 'data(name)' } },
                { selector: 'edge', style: { 'width': 2, 'line-color': '#ccc' } },
                { selector: '.highlighted', style: {'z-index': 100, 'background-color': '#ffd500', 'line-color': '#ffd500' } }
            ]
        });

        // Dictionary to access node ids by name
        let nodeDict = [];
        cy.nodes().forEach(node => nodeDict.push( {key: node.data('name'), value: node.id()} ));
        console.log('number nodes: '+nodeDict.length);
        // Update sample slider max
        updateSampleMax(cy);
        //styleNodes(cy, inputNode);
        layout(cy, inputNode);
        // Make tooltips for all elements
        makeTips(cy);

        // Initialize Gene Data Column with fetched data
        const datacontainer = document.getElementById('data-container');
        datacontainer.innerHTML = ''; // Clear previous rows

        cy.nodes().forEach(node => {
            row = document.createElement('tr');
    
            const cellName = document.createElement('td');
            const geneName = node.data('name'); // Get the gene name
            const link = document.createElement('a');
            
            // Set the href attribute to the desired URL (customize this URL as needed)
            link.href = `https://depmap.org/portal/gene/${geneName}?tab=overview`; // Replace with actual URL
            link.textContent = geneName; // Set the text to the gene name
            link.target = '_blank'; // Open the link in a new tab (optional)

            cellName.appendChild(link);
    
            cellStatus = document.createElement('td');
            cellStatus.textContent = node.data('oncogene');
    
            cellWeight = document.createElement('td');
            edges = node.edgesWith(cy.$(nodeDict[inputNode]));
            cellWeight.textContent = String(edges[0]?.data('weight').toFixed(3) ?? 0);

            row.appendChild(cellName);
            row.appendChild(cellStatus);
            row.appendChild(cellWeight);
            datacontainer.appendChild(row);
        });

        // Enlarge elements on tap
        cy.on('tap', 'edge', (event) => {
            const edge = event.target;
            const width = Number(edge.style('width').replace('px',''));
            const scale = 3;
            const newWidth = edge.hasClass('highlighted') ? width*scale : width/scale;
            edge.animate({
                style: { 'width': newWidth } // Increase edge width
                }, {
                duration: 300,       // Duration in ms
                easing: 'ease-in-out'
            });
        });
        cy.on('tap', 'node', (event) => {
            const node = event.target;
            const size = node.data('size');
            const scale = 1.3;
            const newSize = node.hasClass('highlighted') ? size*scale : size/scale;
            node.animate({
                style: { 'width': newSize, 'height': newSize } // Increase size
                }, {
                duration: 300,       // Duration in ms
                easing: 'ease-in-out'
            });
        });

    } catch (error) {
        alert(error.message);
    }
}

// Set tooltip content
function createTooltipContent(ele) {
    let content = '';
    if (ele.isNode()) {
        let template = document.getElementById('node-template');
        template.querySelector('#ntip-name').textContent = ele.data('name') || 'N/A';
        template.querySelector('#ntip-oncogene').textContent = ele.data('oncogene') || 'N/A';
        template.querySelector('#ntip-nsamples').textContent = '?';// ele.data('lenunion') || 'N/A';
        content = template.innerHTML;
    }
    else {
        let template = document.getElementById('edge-template');
        template.querySelector('#etip-name').textContent = ele.data('name') || 'N/A';
        template.querySelector('#etip-weight').textContent = ele.data('weight').toFixed(3) || 'N/A';
        template.querySelector('#etip-nsamples').textContent = ele.data('lenunion') || 'N/A';
        template.querySelector('#etip-samples').textContent = ele.data('union').join(', ') || 'N/A';
        content = template.innerHTML;
    }
    return content;
  }

function makeTips(cy) {
    if (!cy) { return }
    // Dict to store tooltips in case later reference needed
    const tooltips = {};
    cy.elements().forEach((ele) => {
        // Get the type (node or edge)
        const theme = ele.isNode() ? 'node' : 'edge';
        // Get the properties to show in the tooltip content
        const content = createTooltipContent(ele);

        const popperRef = ele.popperRef();
        // Create tooltip
        const tooltip = tippyFactory(popperRef, content, theme);
        // Show/hide tooltip on click
        ele.on('tap', () => {
            ele.toggleClass('highlighted');
            tooltip.state.isVisible ? tooltip.hide() : tooltip.show();
        });
        tooltips[ele.id()] = tooltip;
    });
}

function layout(cy, input) {
    if (!cy) { return }
    const radius = 40;
    // const center = cy.nodes(`[name = "${input}"]`);
    cy.nodes().forEach(node => {
        if (node.data('name') === input) {
            const size = radius*(1.5);
            node.style({ 'width': size, 'height': size });
            node.data('size', size);
        }
        else {
            const edges = node.edgesWith(cy.nodes(`[name = "${input}"]`));
            const scale = edges.reduce((sum, edge) => sum + edge.data('weight'), 0);
            const size = radius*(scale);
            node.style({ 'width': size, 'height': size });
            node.data('size', size);
        }
    });
    cy.layout({
        name: 'fcose',
        gravity: 1.5,               // Higher gravity pulls larger nodes more centrally
        gravityRange: 1.0,          // Smaller range keeps nodes closer to center
        idealEdgeLength: (edge) => {
          // Larger nodes = edge length, closer to the center
          const sourceSize = edge.source().data('size');
          const targetSize = edge.target().data('size');
          return 100 - 1.5*Math.min(sourceSize, targetSize);
        },
        nodeRepulsion: (node) => {
          // Larger nodes have lower repulsion to stay closer
          return 4500 - 100*node.data('size');
        },
        animate: true,
        animationDuration: 700
      }).run();
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

// const cyContainer = document.getElementById('cy');
// cyContainer.addEventListener('mouseup', () => {
//     cy.resize();
// });