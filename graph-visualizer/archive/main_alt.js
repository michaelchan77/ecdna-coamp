// new version meant to handle large networks with non-oncogenes included

$(document).ready(function() {
    // initialize vars
    let cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [],
        style: []
        // layout: { name: 'fcose' }
    });
    let currentSubset = null;
    let nonOncogenesSubset = null;
    // let inputNode = null;
    const nameToId = {};
    
    // load network data
    function loadNetworkData(url) {
        fetch(url)
        .then(response => response.json())
        .then(data => {
            cy.batch(function() {
                cy.json(data);
                cy.style()
                .resetToDefault()
                // define a class for selected nodes
                .selector('.highlighted-node')
                .style({
                    'background-color': function(ele) { 
                        return ele.data('oncogene_status') ? '#CF5753' : '#87908E';
                    }
                })
                // define a class for selected edges
                .selector('.highlighted-edge')
                .style({
                    'line-color': '#87908E',
                    'line-opacity': 0.5
                })
                .update();
                cy.fit();
                cy.elements().hide();
            });
            cy.nodes().forEach(node => {
                const name = node.data('name');
                const id = node.id();
                nameToId[name] = id;
            });
            document.getElementById('storedText').textContent = 'Ready';
        })
        .catch(error => console.error('Error loading network data:', error));
    }
    loadNetworkData('ccle_network.cyjs');
    // load stylesheet
    /*
    function loadStylesheet(url) {
        fetch(url)
        .then(response => response.json())
        .then(stylesheet => {
            // modify the stylesheet to include functions
            stylesheet.forEach(rule => {
                if (rule.selector === 'node') {
                    rule.style['background-color'] = function(ele) {
                        return ele.data('oncogene_status') ? '#CF5753' : '#87908E';
                    };
                }
            });
            // apply the stylesheet to Cytoscape
            cy.batch(function() {
                cy.style(stylesheet).update();
            });
        })
        .catch(error => console.error('Error loading stylesheet:', error));
    }
    */
    // loadStylesheet('stylesheet.json');
    
    // lock the display (when entire graph is shown)
    function lockDisplay(flag) {
        cy.userZoomingEnabled(!flag);
        cy.userPanningEnabled(!flag);
        cy.boxSelectionEnabled(!flag);
        cy.autoungrabify(flag);
    }

    // freeze display upon init
    cy.ready(function() {
        lockDisplay(true);
    });

    // show neighborhood of a given gene
    function showSubset(cy, name) {
        // get input gene by name
        let inputNode = cy.getElementById(nameToId[name]);
        cy.elements().hide();
        if (inputNode.nonempty()) {
            // get subset
            cy.batch(function() {
                currentSubset = inputNode.closedNeighborhood();
                currentSubset.nodes().addClass('highlighted-node');
                currentSubset.edges().addClass('highlighted-edge');
                currentSubset.show();
            });
            // fit the viewport to the subset
            cy.fit(currentSubset);
            lockDisplay(false);

            // Update visible elements based on the current slider value
            updateVisibleElements();
        }
        else {
            currentSubset = null;
            lockDisplay(true);
        }
    }

    // Function to update visible elements of subset based on sliders
    function updateVisibleElements() {
        if (currentSubset == null) return; // Do nothing if no subset is selected

        let sliderValue = parseFloat($('#edgeWeight').val());
        let sampleVal = parseInt($('#numSamples').val());
        
        // const testStr = "";

        // Show all edges within subset
        currentSubset.show();
        // Hide edges with weight < slider value or num samples <
        currentSubset.edges().forEach(function(edge) {
            var weight = edge.data('weight') || 0;
            // var numSamples = edge.data('total_samples') || 0;
            // testStr = numSamples;
            if (weight < sliderValue) {// || numSamples < sampleVal) {
                edge.hide();
                edge.connectedNodes(`[name != "${$('#textBox').val()}"]`).hide();
            }
        });
        // fit the viewport to the remaining visible elements
        cy.fit(currentSubset);
        // document.getElementById('titleText').textContent = testStr;

        // // Alt approach: Filter edges within the subset based on the slider value
        // var visibleEdges = currentSubset.edges().filter(function(edge) {
        //     var weight = edge.data('weight') || 0;
        //     return weight >= sliderValue;
        // });
    }

    // Button click handler
    $('#storeButton').on('click', function() {
        const textBoxValue = $('#textBox').val().trim();
        if (cy) { // Ensure Cytoscape instance is initialized
            document.getElementById('storedText').textContent = nameToId[textBoxValue] || 'Gene not found';
            showSubset(cy, textBoxValue);
        }
    });
    // Slider handlers
    $('#edgeWeight').on('input', function() {
        if (cy) {
            updateVisibleElements();
        }
    });
    $('#numSamples').on('input', function() {
        if (cy) {
            updateVisibleElements();
        }
    });
    // Checkbox handler
    document.getElementById('oncogenes_only').addEventListener('change', toggleOncogenes);
    function toggleOncogenes() {
        const isChecked = document.getElementById('oncogenes_only').checked;

        if (isChecked) {
            nonOncogenesSubset = cy.remove('node[!oncogene_status]'); //, edge[source = ], edge[source = ]');
        } else {
            cy.add(nonOncogenesSubset);
            nonOncogenesSubset = null;
        }
    }
});