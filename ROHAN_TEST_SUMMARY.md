# Rohan Journey Test Case Summary

## Overview
This document summarizes the comprehensive test scenarios created for Rohan S. (M001), including the negative case where his mission transitions from "high value" to "at risk" and back to normal.

## Test Scenarios Added

### 1. **Positive Journey Flow** (Already Existed)
- **Loyal Member** → **Opportunity Detected** → **Consideration** → **Multi-Product Member**
- Mission: Investment Product Adoption
- Duration: 10-15 minutes (6-8 conversations)

### 2. **NEGATIVE CASE: At Risk Transition** (NEW)
- **Multi-Product Member** → **At Risk**
- Mission Switch: Investment Product Adoption → **High-Value Retention**
- Trigger: Fee complaints, competitor mentions, service dissatisfaction
- Duration: 5-10 minutes (3-4 negative conversations)

#### Negative Conversation Examples:
```
- "I just noticed the account maintenance fees are quite high. Why am I being charged so much?"
- "I saw that other banks are offering zero maintenance fees. I'm thinking of switching."
- "The customer service has been really slow lately."
- "I'm considering moving most of my funds to another bank."
```

### 3. **RECOVERY: Re-engagement Phase** (NEW)
- **At Risk** → **Re-engagement** → **Retained Member**
- Mission: High-Value Retention (continued)
- Actions: Retention offers, fee waivers, premium account upgrades
- Duration: 10-15 minutes (4-6 conversations)

#### Recovery Conversation Examples:
```
- "What can you do to keep me as a customer? I need a better deal."
- "If you waive the fees for 12 months, I'll consider staying."
- "Tell me more about the premium account benefits you mentioned."
- "Okay, that sounds fair. Let's upgrade my account to premium with the fee waiver."
- "Thanks for working with me on this. I appreciate the effort."
```

### 4. **Return to Normal** (NEW)
- **Retained Member** → Back to **Investment Product Adoption**
- Mission Switch: High-Value Retention → **Investment Product Adoption**
- Trigger: Growth-minded conversations (SIP increase, new investments)
- Duration: 5 minutes (1-2 conversations)

#### Return to Normal Example:
```
- "Now that my account is sorted, I'd like to increase my SIP amount to 8000 per month."
```

## Complete Journey Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    POSITIVE INVESTMENT JOURNEY                   │
│  Loyal Member → Opportunity Detected → Consideration →          │
│                    Multi-Product Member                          │
│                                                                  │
│  Mission: Investment Product Adoption ✓                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [NEGATIVE TRIGGER]
                    Fee complaints, dissatisfaction
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    NEGATIVE DISRUPTION                           │
│              Multi-Product Member → At Risk                      │
│                                                                  │
│  Mission Switch: Investment → High-Value Retention 🚨           │
│  Wyzion Analysis: Churn Probability 65-75%                      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [RETENTION ACTIONS]
                    Offers, fee waivers
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RECOVERY PHASE                                │
│        At Risk → Re-engagement → Retained Member                │
│                                                                  │
│  Mission: High-Value Retention (continued) 🔄                   │
│  Wyzion Analysis: Churn Probability 35% → 10%                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [GROWTH SIGNAL]
                    SIP increase, new investments
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    RETURN TO NORMAL                              │
│              Back to Investment Growth Focus                     │
│                                                                  │
│  Mission Switch: Retention → Investment Product Adoption ✓      │
│  Recommendations: Growth & expansion focused                     │
└─────────────────────────────────────────────────────────────────┘
```

## Key Testing Points

### Expected System Behavior

#### At "At Risk" Stage:
- ✅ Priority mission switches to "High-Value Retention"
- ✅ Stage shows "At Risk" with 🚨 indicator
- ✅ Wyzion analysis shows "churn probability: 65-75%"
- ✅ Recommendations: "Schedule retention call", "Waive account fees", "Assign relationship manager"
- ✅ Interaction signals show WARNING or NEGATIVE tags

#### At "Re-engagement" Stage:
- ✅ Stage shows "Re-engagement" with 🔄 indicator
- ✅ Wyzion analysis shows "churn probability: 35-45%"
- ✅ Recommendations: "Complete premium upgrade", "Confirm retention offer"
- ✅ Interaction signals shift to POSITIVE

#### At "Retained Member" Stage:
- ✅ Stage shows "Retained Member" with 💚 indicator
- ✅ Wyzion analysis shows "churn probability: 10-15%"
- ✅ Recommendations: "Monitor satisfaction", "Explore growth opportunities"
- ✅ Ready to switch back to growth mission

#### Return to Investment Focus:
- ✅ Priority mission switches back to "Investment Product Adoption"
- ✅ Recommendations focus on investment growth
- ✅ Stage based on investment journey progress

## Quick Test Instructions

### Option 1: Full Journey Test (30-40 minutes)
Run all phases sequentially to test the complete lifecycle:
1. Start with positive investment conversations
2. Trigger negative disruption with fee complaints
3. Execute recovery with retention offers
4. Return to normal with growth-minded conversations
5. Verify all mission switches and stage transitions

### Option 2: Negative Case Only Test (15-20 minutes)
If Rohan is already at "Multi-Product Member":
1. Start with negative conversations (fees, competitors)
2. Verify mission switch to High-Value Retention
3. Execute recovery conversations
4. Verify return to normal state

### Option 3: Quick Validation (5-10 minutes)
Test just the negative trigger and immediate system response:
1. Send 2-3 negative messages
2. Click "Refresh Intent"
3. Verify mission switch and "At Risk" status
4. Check Wyzion analysis shows churn probability

## Test Checklist

Use the detailed checklist in [TEST_SCENARIOS.md](TEST_SCENARIOS.md#negative-case-testing-checklist) (lines 272-308) for step-by-step validation.

## Files Modified

- **TEST_SCENARIOS.md** - Added comprehensive negative case scenarios for Rohan (lines 113-342)
  - NEGATIVE Stage 1: Multi-Product Member → At Risk
  - RECOVERY Stage 2: At Risk → Re-engagement
  - RECOVERY Stage 3: Re-engagement → Retained Member
  - NEGATIVE CASE TESTING CHECKLIST
  - COMPLETE ROHAN JOURNEY: END-TO-END TEST SCENARIO

## Expected Outcomes

### Mission Priority Detection
The system should intelligently detect which mission is priority based on conversation context:
- **Negative signals** (fees, complaints, competitors) → High-Value Retention becomes priority
- **Growth signals** (investment increases, new products) → Investment Product Adoption becomes priority

### Wyzion AI Analysis
The Wyzion analysis should adapt recommendations based on mission and stage:
- **At Risk:** Focus on preventing churn (retention actions)
- **Re-engagement:** Focus on completing retention (offer acceptance)
- **Retained:** Focus on monitoring and identifying growth opportunities
- **Back to Investment:** Focus on expansion and product adoption

### Interaction Signals
The system should track behavioral signals:
- NEGATIVE signals → trigger retention mission
- WARNING signals → confirm at-risk status
- POSITIVE signals → indicate recovery
- Growth signals → enable return to investment mission

## Usage

1. Open the Flask application (http://localhost:5000)
2. Select "Rohan S. - BFSI" from the member dropdown
3. Follow the conversation scenarios in TEST_SCENARIOS.md
4. Click "🔄 Refresh Intent" after each set of conversations to see stage updates
5. Monitor the Wyzion analysis and recommendations panel
6. Verify mission switches and stage transitions

## Notes

- Allow 2-3 conversations per stage transition for accurate detection
- The AI uses GPT-4o to analyze conversation history and determine appropriate mission/stage
- Mission priority is determined dynamically based on conversation content and interaction signals
- Churn probability percentages should appear in Wyzion analysis during retention mission
- System should seamlessly switch between missions based on member needs

## Success Criteria

A successful test run should demonstrate:
1. ✅ Accurate detection of negative sentiment triggering mission switch
2. ✅ Appropriate retention-focused responses during "At Risk" stage
3. ✅ Progressive stage transitions during recovery (At Risk → Re-engagement → Retained)
4. ✅ Churn probability metrics in Wyzion analysis
5. ✅ Successful return to Investment mission after stability
6. ✅ Natural conversation flow throughout all transitions

---

**Last Updated:** October 22, 2025
**Total Test Scenarios:** 15+ conversation examples across all phases
**Estimated Full Test Duration:** 30-40 minutes
