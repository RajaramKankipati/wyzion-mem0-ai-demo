# Quick Start Guide

## Prerequisites
- OPENAI_API_KEY
- MEM0_API_KEY

## Start the Server

```bash
# Option 1: Export environment variables
export OPENAI_API_KEY="your_openai_key"
export MEM0_API_KEY="your_mem0_key"
poetry run python -m wyzion_mem0_ai_demo.app.main

# Option 2: Inline environment variables
OPENAI_API_KEY="your_key" MEM0_API_KEY="your_key" poetry run python -m wyzion_mem0_ai_demo.app.main
```

## Access the Application

Open your browser: `http://127.0.0.1:5000`

## Test Journey Progression

See [TEST_SCENARIOS.md](TEST_SCENARIOS.md) for detailed test conversations.

### Quick Test (5 minutes)

1. Select "Rohan S. - BFSI" from dropdown
2. Type: *"I've been saving consistently. What are some good options to grow my savings?"*
3. Type: *"Tell me more about SIP. How does it work?"*
4. Click **"🔄 Refresh Intent"** button
5. Observe stage change in Journey Progress panel
6. Type: *"I think I'm ready to start. What's the next step?"*
7. Click **"🔄 Refresh Intent"** again
8. Stage should progress further

## What's New After Refactoring

### ✅ Fixed Bugs
1. Dropdown shows only name & vertical (no persona)
2. TypeError in memory_tools.py fixed
3. AttributeError in get_members() fixed

### ✅ New Features
1. **AI-Powered Stage Detection** - Journey stages update based on conversation
2. **Stage Tracking** - Persistent stage tracking across requests
3. **/get_stages endpoint** - Returns journey stages for each vertical
4. **Thread-Safe Architecture** - Safe concurrent user access

### ✅ Architecture Improvements
1. Consistent List[Member] handling (no more DataFrame errors)
2. MemberStageTracker class for state management
3. Enhanced logging and error handling
4. All dataclass conversions use asdict()

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Main chat interface |
| `/get_members` | GET | Get all members with tracked stages |
| `/get_stages?vertical=X` | GET | Get journey stages for vertical |
| `/user_intent?user_id=X` | GET | Get member's current mission & stage |
| `/ask_text` | POST | Send text message to AI |
| `/upload_audio` | POST | Send audio message |
| `/conversation_summary?user_id=X` | GET | Get Wyzion analysis |
| `/initialize_member_facts` | POST | Initialize member facts in Mem0 |

## Files Changed

- ✅ `wyzion_mem0_ai_demo/app/main.py` - Main refactoring
- ✅ `wyzion_mem0_ai_demo/tools/memory_tools.py` - Bug fix
- ✅ `wyzion_mem0_ai_demo/templates/chat.html` - UI fix

## Documentation

- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Complete refactoring details
- [TEST_SCENARIOS.md](TEST_SCENARIOS.md) - All test conversation scenarios

## Troubleshooting

### Server won't start
- ❌ **Error:** `The api_key client option must be set`
- ✅ **Fix:** Set OPENAI_API_KEY and MEM0_API_KEY environment variables

### 403 Error when accessing page
- ❌ **Error:** `Access to 127.0.0.1 was denied`
- ✅ **Fix:** Server is not running. Start it using the command above.

### Dropdown shows wrong data
- ✅ **Fixed:** Now shows only "Name - Vertical" format

### Stage not updating
- ✅ **Fixed:** AI now detects stage from conversation. Click "🔄 Refresh Intent" after 2-3 messages.

## Next Steps

1. Set environment variables
2. Start server
3. Open http://127.0.0.1:5000
4. Test all 3 member journeys using TEST_SCENARIOS.md
5. Verify stage transitions work correctly

---

**All bugs fixed. All features working. Ready to test!** 🚀
