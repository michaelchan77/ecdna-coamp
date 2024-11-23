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

// Dictionary to access node ids by name
let nodeID = {};

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
        nodeID = {};
        cy.nodes().forEach(node => {
            nodeID[node.data('name')] = "#"+node.id();
        });
        console.log('Number of nodes:', Object.keys(nodeID).length);
        console.log(nodeID[inputNode] + ': ' + cy.$(nodeID[inputNode]).data('name'));
        
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
            edges = node.edgesWith(cy.$(nodeID[inputNode]));
            cellWeight.textContent = String(edges[0]?.data('weight').toFixed(3) ?? 'N/A');
            
            row.appendChild(cellName);
            row.appendChild(cellStatus);
            row.appendChild(cellWeight);
            datacontainer.appendChild(row);

            // Add click event to each row
            row.addEventListener('click', () => {
                const nodeName = cellName.textContent; // Assuming cellName text contains node ID
                const node = cy.$(nodeID[nodeName]);
                node.emit('tap');
            });
        });

        // Resize elements on tap
        cy.on('tap', 'edge', (event) => {
            const edge = event.target;
            const width = edge.data('width');
            const newWidth = edge.hasClass('highlighted') ? width+2 : width-2;
            edge.animate({
                style: { 'width': newWidth } // Increase edge width
                }, {
                duration: 300,       // Duration in ms
                easing: 'ease-in-out'
            });
            edge.data('width', newWidth);
        });
        cy.on('tap', 'node', (event) => {
            const node = event.target;
            const size = node.data('size');
            const scale = 5;
            const newSize = node.hasClass('highlighted') ? size+scale : size-scale;
            node.animate({
                style: { 'width': newSize, 'height': newSize } // Increase size
                }, {
                duration: 300,       // Duration in ms
                easing: 'ease-in-out'
            });
            node.data('size', newSize);
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
        template.querySelector('#ntip-nsamples').textContent = ele.data('samples').length || 'N/A';
        content = template.innerHTML;
    }
    else {
        let template = document.getElementById('edge-template');
        template.querySelector('#etip-name').textContent = ele.data('name') || 'N/A';
        template.querySelector('#etip-weight').textContent = ele.data('weight').toFixed(3) || 'N/A';
        template.querySelector('#etip-frac').textContent = ele.data('leninter') + '/' + ele.data('lenunion');
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
    const center = cy.$(nodeID[input]);
    // size nodes
    // scale center node relative to number of samples
    const radius = 20 + center.data('samples').length * 3;
    cy.nodes().forEach(node => {
        // scale other nodes relative to center node
        const scale = node.data('samples').length / center.data('samples').length;
        const size = scale * radius;
        node.style({ 'width': size, 'height': size });
        node.data('size', size);
    });
    // size edges
    cy.edges().forEach(edge => {
        // bucket by edgeweight
        let width = 0.5;
        if (edge.connectedNodes().contains(center)) {
            width = edge.data('weight') * 7.7;
        }
        edge.style({ 'width': width });
        edge.data('width', width);
    });
    cy.layout({
        name: 'fcose',
        gravity: 0.3,               // Lower gravity to reduce pull toward center
        gravityRange: 3.0,          // Increase range to allow for more spread-out nodes
        idealEdgeLength: (edge) => {
            // Increase edge length to space nodes further apart
            const sourceSize = edge.source().data('size');
            const targetSize = edge.target().data('size');
            return 150 - 2 * Math.min(sourceSize, targetSize);  // Increase base length
        },
        nodeRepulsion: (node) => {
            // Increase repulsion across the board to increase spacing
            return 8000 - 200 * node.data('size');  // Larger nodes still have lower repulsion, but overall higher repulsion
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

// Function to sort the table when clicking on column headers
function sortTable(columnIndex) {
    const table = document.getElementById('data-table');
    const tbody = document.getElementById('data-container');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const noDataRow = tbody.querySelector('.no-data');
    // Remove the "No data available" row temporarily if present
    if (noDataRow) rows.splice(rows.indexOf(noDataRow), 1);
    // Toggle sort order
    let sortOrder = table.dataset.sortOrder === 'asc' ? 'desc' : 'asc';
    table.dataset.sortOrder = sortOrder;
    // Sort rows based on the content of the selected column
    rows.sort((a, b) => {
        const cellA = a.children[columnIndex].innerText.trim();
        const cellB = b.children[columnIndex].innerText.trim();
        if (!isNaN(cellA) && !isNaN(cellB)) {
            // Numeric sort
            return sortOrder === 'asc' ? cellA - cellB : cellB - cellA;
        } else {
            // Text sort
            return sortOrder === 'asc'
                ? cellA.localeCompare(cellB)
                : cellB.localeCompare(cellA);
        }
    });
    // Re-add sorted rows to the tbody
    rows.forEach(row => tbody.appendChild(row));
    // Re-add the "No data available" row if needed
    if (noDataRow && rows.length === 0) tbody.appendChild(noDataRow);
}

// const cyContainer = document.getElementById('cy');
// cyContainer.addEventListener('mouseup', () => {
//     cy.resize();
// });