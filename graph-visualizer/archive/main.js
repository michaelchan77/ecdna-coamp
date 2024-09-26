$(document).ready(function() {
    var cy;
    var currentSubset = null;
    var inputNode = null;
    //$.getJSON("a-bcd_network.cyjs", function (data) {
    $.getJSON("ccle_oncogenes.cyjs", function (data) {
        // initialize Cytoscape
        cy = cytoscape({
            container: document.getElementById('cy'), // container to render the graph

            elements: data.elements,

            style: [
                {
                    selector: 'node',
                    style: {
                        'width': 15,
                        'height': 15,
                        'background-color': 'white',
                        // label
                        'label': 'data(name)',
                        'color': 'white',
                        'font-size': 8
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 1.5,
                        'line-color': 'mapData(weight, 0, 1, yellow, purple)'                        
                    }
                }
            ],

            layout: { // Define the layout of the elements
                name: 'fcose',
                animate: false,
                avoidOverlap: true
            }
        });
        // Once the network is loaded, hide all elements
        // cy.elements().hide();
    });

    function showSubset(cy, name) {
        // Show only elements with the specified name
        inputNode = cy.elements(`[name = "${name.trim()}"]`);
        if (inputNode.nonempty()) {
            // Hide all elements
            cy.elements().hide();

            currentSubset = inputNode.closedNeighborhood();
            currentSubset.show();

            // Optionally fit the viewport to the subset
            cy.fit(currentSubset);

            // Update visible elements based on the current slider value
            updateVisibleElements();
        }
        else {
            cy.elements().show();
            currentSubset = null;
            cy.fit();
        }
    }

    // Function to update visible elements of subset based on edge weight
    function updateVisibleElements() {
        if (currentSubset == null) return; // Do nothing if no subset is selected

        var sliderValue = parseFloat($('#edgeWeight').val());

        // Show all edges within subset
        currentSubset.show();
        // Hide edges with weight less than slider value
        currentSubset.edges().forEach(function(edge) {
            var weight = edge.data('weight') || 0;
            if (weight < sliderValue) {
                edge.hide();
                edge.connectedNodes(`[name != "${$('#textBox').val()}"]`).hide();
            }
        });

        // // Filter edges within the subset based on the slider value
        // var visibleEdges = currentSubset.edges().filter(function(edge) {
        //     var weight = edge.data('weight') || 0;
        //     return weight >= sliderValue;
        // });
        
        // Optionally fit the viewport to the remaining visible elements
        // cy.fit(currentSubset);
    }

    // Button click handler
    $('#storeButton').on('click', function() {
        var textBoxValue = $('#textBox').val();
        if (cy) { // Ensure Cytoscape instance is initialized
            showSubset(cy, textBoxValue);
        }
    });
    // Handle edgeweight slider input change
    $('#edgeWeight').on('input', function() {
        if (cy) {
            updateVisibleElements();
        }
    });
});