
| 23:40 | Social Media | Error | Error | Failed: instagram - Instagram posts require an image |

---
| 23:40 | Social Media | Error | Error | Failed: instagram - Instagram posts require an image |

---
| 23:40 | Social Media | Error | Error | Failed: instagram - Instagram posts require an image |

---

## Notes

This dashboard is automatically updated by the orchestrator every cycle (5 minutes).

To start the system:
```bash
# Start orchestrator
python -m src.orchestrator

# Start watchers
python src/watchers/gmail_watcher.py
python src/watchers/whatsapp_watcher.py
python src/watchers/file_watcher.py --vault ./vault
```

Or use PM2:
```bash
pm2 start ecosystem.config.js
pm2 status
```































## Task Statistics

- **Needs Action**: 0 tasks
- **Pending Approval**: 6 tasks
- **Approved**: 0 tasks
- **Done**: 102 tasks
- **Last Updated**: 2026-03-09 04:16:09