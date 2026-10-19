const fs = require('fs');
const path = require('path');

const srcPublic = path.join(__dirname, 'src', 'public');
const distPublic = path.join(__dirname, 'dist', 'public');
const srcDataset = path.join(__dirname, 'src', 'storage', 'dataset.json');
const distStorage = path.join(__dirname, 'dist', 'storage');
const distDataset = path.join(distStorage, 'dataset.json');

fs.mkdirSync(distPublic, { recursive: true });
fs.cpSync(srcPublic, distPublic, { recursive: true });

fs.mkdirSync(distStorage, { recursive: true });
fs.copyFileSync(srcDataset, distDataset);
console.log('[Build] Copied public UI assets and dataset.json to dist.');
