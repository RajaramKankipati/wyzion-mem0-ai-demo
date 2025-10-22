# Quick Guide: Rohan Negative Case Test Scenario

## Overview
This guide provides step-by-step instructions for testing Rohan's journey including the negative case where his status goes from "high value" to "at risk" and recovers back to normal.

## What Was Created

### 1. Comprehensive Test Scenarios
**File:** [TEST_SCENARIOS.md](TEST_SCENARIOS.md) (Lines 113-342)

Added detailed test scenarios covering:
- ✅ Negative case conversations (fees, complaints, competitors)
- ✅ Recovery conversations (retention offers, re-engagement)
- ✅ Return to normal conversations (growth signals)
- ✅ Testing checklist with validation points
- ✅ Complete end-to-end journey test (30-40 minutes)

### 2. Optional Negative Interaction Signals
**File:** [wyzion_mem0_ai_demo/data/models.py](wyzion_mem0_ai_demo/data/models.py) (Lines 208-245)

Added commented-out negative interaction signals that can be enabled for testing:
- 🚨 Multiple Fee Complaints
- ⚠️ Competitor Comparison Detected
- ❌ Service Quality Concern

### 3. Test Summary Documentation
**File:** [ROHAN_TEST_SUMMARY.md](ROHAN_TEST_SUMMARY.md)

Complete overview with visual journey flow diagram and success criteria.

## Quick Start: Run the Negative Case Test

### Prerequisites
1. Start the Flask application:
   ```bash
   cd /Users/rajaramkankipati/wyzion-mem0-ai-demo
   python -m wyzion_mem0_ai_demo.app.main
   ```

2. Open browser to: http://localhost:5000

3. Select "Rohan S. - BFSI" from the member dropdown

### Phase 1: Establish Baseline (Optional - 5 minutes)
If Rohan is not yet at "Multi-Product Member" stage, run these conversations first:

```
1. "I've been saving consistently. What are some good options to grow my savings?"
2. "Tell me more about SIP. How does it work?"
3. Click "🔄 Refresh Intent"
4. "I think I'm ready to start. What's the next step?"
5. Click "🔄 Refresh Intent"
```

**Expected Result:** Rohan should be at "Multi-Product Member" stage in Investment Product Adoption mission.

### Phase 2: Trigger Negative Case (5-10 minutes)

Send these conversations to trigger the "At Risk" status:

```
1. "I just noticed the account maintenance fees are quite high. Why am I being charged so much?"

   [Wait for AI response]

2. "I saw that other banks are offering zero maintenance fees. I'm thinking of switching."

   [Wait for AI response]

3. Click "🔄 Refresh Intent"

   ✅ VERIFY: Mission should switch to "High-Value Retention"
   ✅ VERIFY: Stage should show "At Risk" 🚨
   ✅ VERIFY: Wyzion analysis should show "churn probability: 65-75%"

4. "I'm considering moving most of my funds to another bank. What do you have to say about that?"

   [Wait for AI response - should be retention-focused]

5. Click "🔄 Refresh Intent"

   ✅ VERIFY: Stage remains "At Risk"
   ✅ VERIFY: Recommendation includes retention actions (fee waiver, relationship manager call)
```

**What to Look For:**
- AI responses should be empathetic and focused on retention
- Wyzion panel should show churn probability percentage
- Recommendations should focus on preventing churn
- Mission should automatically switch to "High-Value Retention"

### Phase 3: Recovery - Re-engagement (5-10 minutes)

Send these conversations to show interest in staying:

```
1. "What can you do to keep me as a customer? I need a better deal."

   [Wait for AI response - should present retention offers]

2. "If you waive the fees for 12 months, I'll consider staying."

   [Wait for AI response - should confirm ability to waive fees]

3. Click "🔄 Refresh Intent"

   ✅ VERIFY: Stage should move to "Re-engagement" 🔄
   ✅ VERIFY: Churn probability should decrease to 35-45%

4. "Tell me more about the premium account benefits you mentioned."

   [Wait for AI response - should detail premium benefits]

5. Click "🔄 Refresh Intent"

   ✅ VERIFY: Stage remains "Re-engagement"
   ✅ VERIFY: Positive interaction signals appear
```

**What to Look For:**
- AI responses should focus on value proposition and benefits
- Churn probability should be decreasing
- Interaction signals should shift from negative to positive
- Stage should progress to "Re-engagement"

### Phase 4: Full Recovery (5-10 minutes)

Send these conversations to complete the recovery:

```
1. "Okay, that sounds fair. Let's upgrade my account to premium with the fee waiver."

   [Wait for AI response - should celebrate decision]

2. Click "🔄 Refresh Intent"

   ✅ VERIFY: Stage should move to "Retained Member" 💚
   ✅ VERIFY: Churn probability should drop to 10-15%

3. "Thanks for working with me on this. I appreciate the effort to keep me as a customer."

   [Wait for AI response - should acknowledge and thank]

4. "The premium account is much better. I'm glad I stayed."

   [Wait for AI response - should celebrate positive feedback]

5. Click "🔄 Refresh Intent"

   ✅ VERIFY: Stage remains "Retained Member"
   ✅ VERIFY: Recommendations shift to monitoring and growth opportunities
```

**What to Look For:**
- AI responses should celebrate the successful retention
- Churn probability should be at lowest level
- Recommendations should start mentioning growth opportunities
- Member should be stable and satisfied

### Phase 5: Return to Normal (5 minutes)

Send growth-minded conversations to switch back to investment focus:

```
1. "Now that my account is sorted, I'd like to increase my SIP amount to 8000 per month."

   [Wait for AI response - should support investment growth]

2. Click "🔄 Refresh Intent"

   ✅ VERIFY: Mission may switch back to "Investment Product Adoption"
   ✅ VERIFY: Recommendations focus on investment growth
   ✅ VERIFY: System recognizes return to growth mindset

3. "I'm also interested in exploring other mutual fund options now."

   [Wait for AI response - should provide investment guidance]
```

**What to Look For:**
- AI responses should focus on investment guidance
- Mission priority should shift back to Investment Product Adoption
- Recommendations should focus on growth and expansion
- System should recognize the member is back to normal, growth-oriented state

## Success Criteria Checklist

After completing all phases, verify:

- [ ] Mission successfully switched from Investment → Retention when negative signals detected
- [ ] Stage progressed: Multi-Product → At Risk → Re-engagement → Retained Member
- [ ] Wyzion analysis showed churn probability percentages (decreasing from 70% → 10%)
- [ ] AI responses adapted to each stage (defensive → retention → growth)
- [ ] Recommendations evolved appropriately (churn prevention → offer completion → monitoring → growth)
- [ ] Interaction signals reflected the journey (positive → negative → warning → positive)
- [ ] Mission switched back to Investment focus after stability achieved
- [ ] Conversation flow felt natural and member-centric throughout

## Enabling Optional Negative Interaction Signals (Advanced)

If you want the interaction signals panel to show pre-existing negative signals:

1. Open [wyzion_mem0_ai_demo/data/models.py](wyzion_mem0_ai_demo/data/models.py)
2. Navigate to lines 208-245
3. Uncomment the three negative interaction entries
4. Restart the Flask application
5. Refresh the browser

This will add visible negative signals in the interaction panel that support the "At Risk" narrative.

## Troubleshooting

### Issue: Stage not updating after negative conversations
**Solution:**
- Ensure you're clicking "🔄 Refresh Intent" after 2-3 conversations
- Try more explicit negative language (mention "switch banks", "close account", "competitors")
- Check that both missions exist in sample_missions()

### Issue: Mission not switching to High-Value Retention
**Solution:**
- Verify models.py contains both missions (Investment Product Adoption and High-Value Retention)
- Use stronger churn signals in conversations
- Check application logs for mission detection debug messages

### Issue: Churn probability not showing in Wyzion analysis
**Solution:**
- Ensure the conversation clearly indicates retention concerns
- The risk_level in member data should reflect the situation
- Check that the priority mission is correctly identified as High-Value Retention

### Issue: AI responses not retention-focused during "At Risk"
**Solution:**
- Verify the priority mission detection is working (check logs)
- Ensure the system_message includes retention mission context
- Try more explicit retention-related questions

## Additional Resources

- **Full Test Scenarios:** [TEST_SCENARIOS.md](TEST_SCENARIOS.md)
- **Journey Overview:** [ROHAN_TEST_SUMMARY.md](ROHAN_TEST_SUMMARY.md)
- **Data Models:** [wyzion_mem0_ai_demo/data/models.py](wyzion_mem0_ai_demo/data/models.py)
- **Main Application:** [wyzion_mem0_ai_demo/app/main.py](wyzion_mem0_ai_demo/app/main.py)

## Testing Timeline

- **Quick Validation:** 5-10 minutes (just trigger negative and verify detection)
- **Negative Case Only:** 15-20 minutes (trigger + recovery)
- **Full Journey:** 30-40 minutes (complete lifecycle from loyal member to recovery)

## Notes

- The AI uses conversation history and interaction signals to determine mission priority
- Stage detection happens asynchronously - allow a few seconds after clicking "Refresh Intent"
- The system is designed to prioritize retention when churn signals are detected
- Churn probability is dynamically calculated based on conversation sentiment and signals
- Recovery requires genuine positive engagement, not just single-word responses

---

**Created:** October 22, 2025
**Purpose:** Test negative case scenario for member journey with churn risk and recovery
**Member:** Rohan S. (M001) - BFSI Vertical
**Test Type:** End-to-end journey including negative disruption and recovery
