const express = require('express');
const path = require('path');
const app = express();
const PORT = 5500; 

// Set up static file serving
app.use(express.static(path.join(__dirname))); 

// Send index.html by default for root route "/"
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname,'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running at http://127.0.0.1:${PORT}`);
});