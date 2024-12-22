// screenshotService.js
const { desktopCapturer } = require('electron');
const WebSocket = require('ws');

class ScreenshotService {
  constructor(websocketUrl) {
    this.websocketUrl = websocketUrl;
    this.ws = null;
    this.intervalId = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.currentProject = null;
    this.isCapturing = false;
    this.frequency = 5; // Default frequency in seconds

    
    // Connect immediately
    this.connect();
  }

  connect() {
    console.log('Connecting to Screenshot WebSocket...', this.websocketUrl);
    
    try {
      this.ws = new WebSocket(this.websocketUrl);
      
      this.ws.on('open', () => {
        console.log('Screenshot WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // If we were capturing before, restart capture
        if (this.isCapturing && this.currentProject) {
          this.startCapturing(this.currentProject);
        }
      });

      this.ws.on('close', () => {
        console.log('Screenshot WebSocket disconnected');
        this.isConnected = false;
        this.handleReconnect();
      });

      this.ws.on('error', (error) => {
        console.error('Screenshot WebSocket error:', error);
      });

      this.ws.on('message', (data) => {
        try {
          const message = JSON.parse(data);
          if (message.type === 'screenshot_analysis') {
            console.log('Received screenshot analysis:', message.analysis);
          }
        } catch (error) {
          console.error('Error parsing screenshot message:', error);
        }
      });
    } catch (error) {
      console.error('Error creating screenshot WebSocket:', error);
      this.handleReconnect();
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect screenshots (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      setTimeout(() => this.connect(), 5000);
    } else {
      console.error('Max screenshot reconnection attempts reached');
      this.stopCapturing();
    }
  }

  startCapturing(project, frequency = this.frequency) {
      if (!project) {
          console.error('Cannot start capturing without a project');
          return;
      }

      this.currentProject = project;
      this.frequency = frequency;
      this.isCapturing = true;
      
      if (this.intervalId) {
          clearInterval(this.intervalId);
      }

      console.log(`Starting screenshot capture for project: ${project} at ${frequency} second intervals`);
      
      this.intervalId = setInterval(() => {
          this.captureAndSend();
      }, this.frequency * 1000);
      
      // Initial capture
      this.captureAndSend();
  }

  updateFrequency(newFrequency) {
      if (newFrequency !== this.frequency) {
          this.frequency = newFrequency;
          console.log(`Updating screenshot frequency to ${newFrequency} seconds`);
          
          if (this.isCapturing) {
              // Restart capture with new frequency
              this.startCapturing(this.currentProject, newFrequency);
          }
      }
  }

  async captureAndSend() {
    if (!this.isConnected || !this.currentProject || !this.isCapturing) {
      console.log('Screenshot service status check:', { 
        connected: this.isConnected, 
        project: this.currentProject,
        isCapturing: this.isCapturing
      });
      return;
    }

    try {
      console.log('Starting screen capture process...');
      const sources = await desktopCapturer.getSources({
        types: ['screen'],
        thumbnailSize: {
          width: 1920,
          height: 1080
        }
      });

      console.log('Got screen sources:', sources.length);

      if (sources && sources[0]) {
        console.log('Converting screenshot to data URL...');
        const screenshot = sources[0].thumbnail.toDataURL();
        
        const message = JSON.stringify({
          type: 'screenshot',
          data: screenshot,
          project: this.currentProject,
          timestamp: new Date().toISOString()
        });

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          console.log(`Sending screenshot (${(screenshot.length / 1024).toFixed(2)} KB) for project:`, this.currentProject);
          this.ws.send(message);
        } else {
          console.log('WebSocket not ready. Status:', this.ws ? this.ws.readyState : 'no websocket');
          this.connect();
        }
      }
    } catch (error) {
      console.error('Error in captureAndSend:', error);
    }
  }

  stopCapturing() {
    this.isCapturing = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    console.log('Stopped screenshot capture');
  }

  disconnect() {
    this.stopCapturing();
    if (this.ws) {
      this.ws.close();
    }
  }

  setProject(project) {
    this.currentProject = project;
    if (this.isCapturing) {
      // Restart capture with new project
      this.startCapturing(project);
    }
  }
}

module.exports = { ScreenshotService };
