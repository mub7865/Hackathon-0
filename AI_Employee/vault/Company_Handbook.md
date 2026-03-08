# Company Handbook

**Last Updated**: 2026-01-19T00:00:00Z

## Processing Rules

### Summarization
- Always use exactly 3 bullet points for summaries
- Highlight key dates and amounts in bold
- Flag urgent items with 🚨 emoji
- Extract action items as checkboxes
- Keep summaries under 200 words
- Focus on actionable insights, not just description

### Tone & Style
- Professional and courteous tone
- Concise language (avoid jargon unless technical document)
- Action-oriented phrasing ("Review contract" not "Contract needs review")
- Use emojis sparingly for visual clarity
- Write in active voice
- Address user directly when suggesting actions

### Special Instructions
- Flag amounts over $500 with 💰 emoji
- Identify deadlines and add to action items with due date
- Extract contact information (email, phone) when present
- Highlight client names in bold on first mention
- Note any compliance, legal, or regulatory terms
- If document is unclear or incomplete, note what's missing

## Custom Flags

### Financial
- Amount > $500 → 💰 High-value transaction
- Amount > $10,000 → 🚨💰 Critical financial decision
- Invoice → 📊 Financial document
- Payment terms → 💳 Payment information

### Time-Sensitive
- Deadline < 3 days → 🚨 Urgent deadline
- Deadline < 7 days → ⚠️ Upcoming deadline
- "ASAP" or "urgent" → 🚨 Urgent request
- Meeting scheduled → 📅 Calendar event

### Communication
- Client email → 👤 Stakeholder communication
- Internal email → 🏢 Team communication
- External vendor → 🤝 Partner communication

### Document Types
- Contract → 📄 Legal document
- NDA or confidentiality → 🔒 Confidential
- Report or analysis → 📈 Data document
- Meeting notes → 📝 Notes

### Issues
- Error, failure, or problem → ❌ Issue detected
- Risk or concern → ⚠️ Risk identified
- Question or unclear → ❓ Needs clarification

## Preferences

- **Summary length**: 150-200 words
- **Action item format**: Checkboxes with [ ]
- **Date format**: ISO 8601 (YYYY-MM-DD)
- **Time zone**: UTC (convert all times to UTC)
- **Language**: English
- **Emoji usage**: Moderate (flags and status only)
- **Link format**: Wikilinks [[file]] for internal references
- **Number format**: US format (1,000.00)
- **Currency**: USD ($) unless specified otherwise

## Examples

### Good Summary Example
```
**Summary**:
- Client requesting Q4 financial report by Friday (3 days)
- Report should include revenue breakdown and expense analysis
- Stakeholder: john@example.com (CFO)

**Key Points**:
- 🚨 Urgent: Deadline in 3 days
- 📊 Deliverable: Q4 financial report
- 👤 Stakeholder: John Smith (CFO)

**Action Items**:
- [ ] Prepare Q4 revenue breakdown (due: Thu)
- [ ] Compile expense analysis (due: Thu)
- [ ] Review with team before sending (due: Thu)
- [ ] Send to john@example.com (due: Fri)
```

## Notes

- This handbook is read before processing each task
- Changes take effect immediately (no restart required)
- If handbook is missing, AI uses sensible defaults
- You can add custom sections as needed
- AI will do its best to follow rules, but may not be perfect
