const path = require('path');
const electron = require('electron');

// Get the app path differently for development and production
const isProd = process.env.NODE_ENV === 'production';
const getAppPath = () => {
  if (isProd) {
    // In production, use the app's root path
    return path.dirname(electron.app.getPath('exe'));
  } else {
    // In development, use the project root
    return path.join(__dirname, '..');
  }
};

// Define all important paths relative to the app root
const paths = {
  root: getAppPath(),
  get config() {
    return path.join(this.root, 'config');
  },
  get recordings() {
    return path.join(this.root, 'recordings');
  },
  get configFile() {
    return path.join(this.config, 'config.json');
  }
};

// Ensure directories exist
const fs = require('fs');
const ensureDirectoryExists = (dirPath) => {
  if (!fs.existsSync(dirPath)) {
    fs.mkdirSync(dirPath, { recursive: true });
  }
};

// Create necessary directories
ensureDirectoryExists(paths.config);
ensureDirectoryExists(paths.recordings);

// Create default config if it doesn't exist
if (!fs.existsSync(paths.configFile)) {
  const defaultConfig = {
    openai: {
      apiKey: process.env.OPENAI_API_KEY || ''
    },
    recording: {
      format: 'wav',
      sampleRate: 16000
    }
  };
  
  fs.writeFileSync(
    paths.configFile,
    JSON.stringify(defaultConfig, null, 2)
  );
}

module.exports = paths;
