# GitHub Repository Setup Instructions

## Step 1: Create Repository on GitHub

1. **Go to GitHub**: https://github.com/new
2. **Repository name**: `Hackathon-0` (or `hackathon-0`)
3. **Description**: `Bronze Tier AI Assistant - Personal AI Employee Hackathon 0`
4. **Visibility**: Public (recommended for hackathon submission)
5. **DO NOT initialize with**:
   - ❌ README
   - ❌ .gitignore
   - ❌ License
6. **Click**: "Create repository"

## Step 2: Get Your Repository URL

After creating, GitHub will show you a URL like:
```
https://github.com/YOUR_USERNAME/Hackathon-0.git
```

Copy this URL.

## Step 3: Push Code (Run these commands)

```bash
cd /mnt/d/Hackathons/hackathon-0/bronze

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/Hackathon-0.git

# Push to GitHub
git push -u origin main
```

## Step 4: Verify

Go to your repository URL and verify all files are there:
- ✅ src/ folder with all Python code
- ✅ vault/ folder with Obsidian vault
- ✅ README.md
- ✅ QUICK_START.md
- ✅ requirements.txt

## Alternative: Using SSH (if you have SSH keys set up)

```bash
# Add remote with SSH
git remote add origin git@github.com:YOUR_USERNAME/Hackathon-0.git

# Push to GitHub
git push -u origin main
```

## Troubleshooting

### Error: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/Hackathon-0.git
```

### Error: "Authentication failed"
You need to use a Personal Access Token instead of password:
1. Go to: https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scopes: `repo` (full control)
4. Copy the token
5. Use token as password when pushing

### Error: "Permission denied"
Make sure you're logged into the correct GitHub account.

---

**After pushing, your repository will be live at:**
`https://github.com/YOUR_USERNAME/Hackathon-0`
