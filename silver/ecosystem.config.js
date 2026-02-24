module.exports = {
  apps: [
    {
      name: 'silver-orchestrator',
      script: 'run_orchestrator.py',
      interpreter: 'D:/Hackathons/hackathon-0/silver/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/silver',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/silver',
        ANTHROPIC_BASE_URL: 'http://127.0.0.1:3456',
        ANTHROPIC_AUTH_TOKEN: 'test',
        ANTHROPIC_API_KEY: 'test',
        NO_PROXY: '127.0.0.1',
        API_TIMEOUT_MS: '600000',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/silver/vault',
        GMAIL_CREDENTIALS_PATH: 'D:/Hackathons/hackathon-0/silver/.credentials/gmail-credentials.json',
        GMAIL_TOKEN_PATH: 'D:/Hackathons/hackathon-0/silver/.credentials/gmail-token.pickle',
        WHATSAPP_SESSION: 'D:/Hackathons/hackathon-0/silver/sessions/wa_autonomous_v4',
        LINKEDIN_EMAIL: 'muhammadubaidansari145@gmail.com',
        LINKEDIN_PASSWORD: 'ubaid7865'
      },
      error_file: 'logs/orchestrator-error.log',
      out_file: 'logs/orchestrator-out.log',
      time: true
    },
    {
      name: 'silver-gmail-watcher',
      script: 'src/watchers/gmail_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/silver/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/silver',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/silver',
        GMAIL_CREDENTIALS_PATH: 'D:/Hackathons/hackathon-0/silver/.credentials/gmail-credentials.json',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/silver/vault'
      },
      error_file: 'logs/gmail-watcher-error.log',
      out_file: 'logs/gmail-watcher-out.log',
      time: true
    },
    {
      name: 'silver-whatsapp-watcher',
      script: 'src/watchers/whatsapp_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/silver/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/silver',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/silver',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/silver/vault'
      },
      error_file: 'logs/whatsapp-watcher-error.log',
      out_file: 'logs/whatsapp-watcher-out.log',
      time: true
    },
    {
      name: 'silver-linkedin-watcher',
      script: 'src/watchers/linkedin_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/silver/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/silver',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/silver',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/silver/vault'
      },
      error_file: 'logs/linkedin-watcher-error.log',
      out_file: 'logs/linkedin-watcher-out.log',
      time: true,
      autorestart: false  // Disable auto-restart for LinkedIn (optional)
    },
    {
      name: 'silver-file-watcher',
      script: 'src/watchers/file_watcher.py',
      interpreter: 'D:/Hackathons/hackathon-0/silver/venv/Scripts/python.exe',
      cwd: 'D:/Hackathons/hackathon-0/silver',
      env: {
        PYTHONPATH: 'D:/Hackathons/hackathon-0/silver',
        VAULT_PATH: 'D:/Hackathons/hackathon-0/silver/vault'
      },
      error_file: 'logs/file-watcher-error.log',
      out_file: 'logs/file-watcher-out.log',
      time: true
    }
  ]
};
