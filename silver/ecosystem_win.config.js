module.exports = {
  apps: [
    {
      name: 'silver-orchestrator',
      script: 'python',
      args: ['-m', 'src.orchestrator'],
      cwd: 'D:\\Hackathons\\hackathon-0\\silver',
      interpreter: 'none',
      env: {
        PYTHONPATH: '.',
        PYTHONDONTWRITEBYTECODE: '1',
        VAULT_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\vault',
        GMAIL_TOKEN_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\sessions\\gmail_tokens\\token.pickle',
        PATH: 'C:\\Users\\HP\\AppData\\Roaming\\npm;' + process.env.PATH
      }
    },
    {
      name: 'silver-gmail-watcher',
      script: 'src/watchers/gmail_watcher.py',
      cwd: 'D:\\Hackathons\\hackathon-0\\silver',
      interpreter: 'python',
      env: {
        PYTHONPATH: '.',
        PYTHONDONTWRITEBYTECODE: '1',
        VAULT_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\vault',
        GMAIL_TOKEN_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\sessions\\gmail_tokens\\token.pickle'
      }
    },
    {
      name: 'silver-whatsapp-watcher',
      script: 'src/watchers/whatsapp_watcher.py',
      cwd: 'D:\\Hackathons\\hackathon-0\\silver',
      interpreter: 'python',
      env: {
        PYTHONPATH: '.',
        PYTHONDONTWRITEBYTECODE: '1',
        VAULT_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\vault'
      }
    },
    {
      name: 'silver-linkedin-watcher',
      script: 'src/watchers/linkedin_watcher.py',
      cwd: 'D:\\Hackathons\\hackathon-0\\silver',
      interpreter: 'python',
      env: {
        PYTHONPATH: '.',
        PYTHONDONTWRITEBYTECODE: '1',
        VAULT_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\vault'
      }
    },
    {
      name: 'silver-file-watcher',
      script: 'src/watchers/file_watcher.py',
      cwd: 'D:\\Hackathons\\hackathon-0\\silver',
      interpreter: 'python',
      env: {
        PYTHONPATH: '.',
        PYTHONDONTWRITEBYTECODE: '1',
        VAULT_PATH: 'D:\\Hackathons\\hackathon-0\\silver\\vault'
      }
    }
  ]
};
