module.exports = {
  apps: [
    {
      name: 'atlas-orchestrator',
      script: 'run_orchestrator.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        ANTHROPIC_BASE_URL: 'http://127.0.0.1:3456',
        ANTHROPIC_AUTH_TOKEN: 'test',
        ANTHROPIC_API_KEY: 'test',
        NO_PROXY: '127.0.0.1',
        API_TIMEOUT_MS: '600000',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault',
        GMAIL_CREDENTIALS_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/.credentials/gmail-credentials.json',
        GMAIL_TOKEN_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/.credentials/gmail-token.pickle',
        WHATSAPP_SESSION: 'D:/Hackathons/hackathon-0/AI_Employee/sessions/wa_autonomous_v4'
        // LinkedIn credentials are loaded from .env file
      },
      error_file: 'logs/orchestrator-error.log',
      out_file: 'logs/orchestrator-out.log',
      time: true
    },
    {
      name: 'atlas-gmail-watcher',
      script: 'src/watchers/gmail_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        GMAIL_CREDENTIALS_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/.credentials/gmail-credentials.json',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/gmail-watcher-error.log',
      out_file: 'logs/gmail-watcher-out.log',
      time: true
    },
    {
      name: 'atlas-whatsapp-watcher',
      script: 'src/watchers/whatsapp_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/whatsapp-watcher-error.log',
      out_file: 'logs/whatsapp-watcher-out.log',
      time: true
    },
    {
      name: 'atlas-linkedin-watcher',
      script: 'src/watchers/linkedin_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/linkedin-watcher-error.log',
      out_file: 'logs/linkedin-watcher-out.log',
      time: true,
      autorestart: false  // Disable auto-restart for LinkedIn (optional)
    },
    {
      name: 'atlas-file-watcher',
      script: 'src/watchers/file_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/file-watcher-error.log',
      out_file: 'logs/file-watcher-out.log',
      time: true
    },
    {
      name: 'atlas-facebook-watcher',
      script: 'src/watchers/facebook_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/facebook-watcher-error.log',
      out_file: 'logs/facebook-watcher-out.log',
      time: true,
      autorestart: false  // Requires manual login first
    },
    {
      name: 'atlas-instagram-watcher',
      script: 'src/watchers/instagram_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/AI_Employee/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/AI_Employee',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/AI_Employee',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/AI_Employee/vault'
      },
      error_file: 'logs/instagram-watcher-error.log',
      out_file: 'logs/instagram-watcher-out.log',
      time: true,
      autorestart: false  // Requires manual login first
    }
  ]
};
