const express = require('express');
const path = require('path');
const app = express();

app.use(express.static(path.join(__dirname)));
app.get('*', (_, res) => res.sendFile(path.join(__dirname, 'index.html')));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`DAYANA running on port ${PORT}`));
