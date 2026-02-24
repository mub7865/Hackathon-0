# WhatsApp MCP Setup - Options & Guide

## Overview
WhatsApp integration is more complex than Gmail because WhatsApp doesn't have an official MCP server. We have 3 options.

---

## Option 1: WhatsApp Web Automation (Browser MCP) 🟡

**Pros:**
- Free
- Uses existing Browser MCP (Puppeteer)
- No API keys needed

**Cons:**
- Requires phone to stay connected
- Less reliable (web scraping)
- Can break with WhatsApp updates
- Not recommended for production

### Setup Steps:

1. **Install WhatsApp Web automation library:**
```bash
npm install -g whatsapp-web.js
```

2. **Create custom MCP wrapper:**
```javascript
// .mcp-servers/whatsapp-web/index.js
const { Client } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');

const client = new Client();

client.on('qr', (qr) => {
    qrcode.generate(qr, {small: true});
});

client.on('ready', () => {
    console.log('WhatsApp Client is ready!');
});

client.initialize();
```

3. **Add to mcp.json:**
```json
{
  "whatsapp-web": {
    "command": "node",
    "args": [".mcp-servers/whatsapp-web/index.js"]
  }
}
```

**Not recommended for Silver Tier - too unreliable.**

---

## Option 2: Twilio WhatsApp API ✅ (Recommended)

**Pros:**
- Official API
- Reliable and stable
- Easy to integrate
- Good documentation

**Cons:**
- Costs money (~$0.005 per message)
- Requires Twilio account
- Need to verify business

### Setup Steps:

#### Step 1: Create Twilio Account

1. Go to: https://www.twilio.com/try-twilio
2. Sign up for free trial ($15 credit)
3. Verify your phone number
4. Complete account setup

#### Step 2: Enable WhatsApp Sandbox

1. Go to Twilio Console: https://console.twilio.com/
2. Navigate to: **Messaging** → **Try it out** → **Send a WhatsApp message**
3. Follow instructions to join sandbox:
   - Send "join [your-code]" to Twilio WhatsApp number
   - Example: Send "join happy-tiger" to +1 415 523 8886

#### Step 3: Get API Credentials

1. Go to: https://console.twilio.com/
2. Copy these values:
   - **Account SID** (starts with AC...)
   - **Auth Token** (click to reveal)
3. Note the **WhatsApp Sandbox Number** (e.g., whatsapp:+14155238886)

#### Step 4: Add to .env File

```bash
# Twilio WhatsApp Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
TWILIO_YOUR_WHATSAPP=whatsapp:+1234567890  # Your verified number
```

#### Step 5: Install Twilio SDK

```bash
npm install -g twilio
```

#### Step 6: Create Twilio MCP Wrapper

```bash
mkdir -p .mcp-servers/twilio-whatsapp
```

Create file: `.mcp-servers/twilio-whatsapp/index.js`

```javascript
const twilio = require('twilio');

const accountSid = process.env.TWILIO_ACCOUNT_SID;
const authToken = process.env.TWILIO_AUTH_TOKEN;
const client = twilio(accountSid, authToken);

// MCP Server implementation
const server = {
  name: 'twilio-whatsapp',
  version: '1.0.0',

  tools: {
    send_whatsapp: async (params) => {
      const { to, message } = params;

      const result = await client.messages.create({
        from: process.env.TWILIO_WHATSAPP_NUMBER,
        to: `whatsapp:${to}`,
        body: message
      });

      return { success: true, sid: result.sid };
    },

    get_messages: async (params) => {
      const messages = await client.messages.list({
        from: process.env.TWILIO_WHATSAPP_NUMBER,
        limit: params.limit || 20
      });

      return messages.map(m => ({
        from: m.from,
        to: m.to,
        body: m.body,
        date: m.dateCreated
      }));
    }
  }
};

// Start MCP server
console.log('Twilio WhatsApp MCP Server started');
```

#### Step 7: Add to mcp.json

```json
{
  "twilio-whatsapp": {
    "command": "node",
    "args": [".mcp-servers/twilio-whatsapp/index.js"],
    "env": {
      "TWILIO_ACCOUNT_SID": "${TWILIO_ACCOUNT_SID}",
      "TWILIO_AUTH_TOKEN": "${TWILIO_AUTH_TOKEN}",
      "TWILIO_WHATSAPP_NUMBER": "${TWILIO_WHATSAPP_NUMBER}"
    }
  }
}
```

#### Step 8: Test Twilio WhatsApp

```bash
# Test sending a message
ccr code "Use Twilio WhatsApp to send 'Hello from AI!' to my number"
```

---

## Option 3: WhatsApp Business API 💰 (Production)

**Pros:**
- Official WhatsApp Business API
- Most reliable
- Full features (media, templates, etc.)
- Scalable

**Cons:**
- Expensive (requires Meta Business verification)
- Complex setup
- Need business account
- Approval process takes time

### Requirements:
- Meta Business Account
- Verified business
- Phone number dedicated to WhatsApp Business
- Monthly fees (~$50+)

### Setup:
1. Apply for WhatsApp Business API: https://business.whatsapp.com/
2. Complete business verification
3. Set up webhook endpoints
4. Implement custom MCP server

**Not recommended for Silver Tier - too expensive and complex.**

---

## Comparison Table

| Feature | WhatsApp Web | Twilio | Business API |
|---------|-------------|--------|--------------|
| Cost | Free | ~$0.005/msg | $50+/month |
| Reliability | Low | High | Very High |
| Setup Time | 1 hour | 30 minutes | 2-4 weeks |
| Production Ready | ❌ No | ✅ Yes | ✅ Yes |
| Recommended | ❌ | ✅ | For Enterprise |

---

## Recommended Approach for Silver Tier

**Use Twilio WhatsApp API:**
1. Free trial gives $15 credit (~3000 messages)
2. Easy setup (30 minutes)
3. Reliable and production-ready
4. Good for testing and small-scale use

**Steps:**
1. Create Twilio account (free trial)
2. Enable WhatsApp sandbox
3. Add credentials to `.env`
4. Create Twilio MCP wrapper
5. Test with sample message

---

## Example WhatsApp Tasks

### Send WhatsApp Message

```yaml
---
id: whatsapp_send_001
source: manual
type: whatsapp_send
status: pending
priority: high
created: 2026-01-23T17:00:00
---

## Send WhatsApp to Client

**To:** +1234567890
**Message:**
Hi [Client],

Your order #12345 has been shipped!

Tracking: ABC123XYZ

Thanks!
```

### Read WhatsApp Messages

```yaml
---
id: whatsapp_read_001
source: manual
type: whatsapp_read
status: pending
priority: medium
created: 2026-01-23T17:00:00
---

## Check WhatsApp Messages

**Task:** Check for any urgent WhatsApp messages in the last hour and summarize them.
```

---

## Security Notes

1. **Never commit Twilio credentials to git**
2. **Use environment variables** (already configured in .env)
3. **Rotate Auth Token** regularly
4. **Monitor usage** to avoid unexpected charges
5. **Set spending limits** in Twilio console

---

## Troubleshooting

### Issue: "Authentication failed"
**Solution:** Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env

### Issue: "Number not verified"
**Solution:** Join WhatsApp sandbox by sending "join [code]" to Twilio number

### Issue: "Message not delivered"
**Solution:** Ensure recipient has joined sandbox (for testing)

---

## Next Steps

1. **For Testing:** Use Twilio WhatsApp Sandbox (free)
2. **For Production:** Upgrade to Twilio paid plan
3. **For Enterprise:** Consider WhatsApp Business API

**Twilio is the best balance of cost, reliability, and ease of setup for Silver Tier.**
