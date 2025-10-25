# Test Conversation Scenarios for Journey Stage Progression

This document provides conversation test scenarios for each member to smoothly transition through their journey stages.

---

## Member 1: Rohan S. (M001) - BFSI Vertical

**Current Profile:**
- Vertical: BFSI
- Persona: Existing Loyal Member
- Current Stage: Loyal Member
- Goal: Adopt a new investment product (Mutual Fund SIP)
- Credit Score: 720
- Current Products: Checking Account, Savings Account

**Journey Stages:**
1. ✅ Loyal Member (Current)
2. ⚠️ Opportunity Detected
3. 🤔 Consideration
4. 🌟 Multi-Product Member

---

### Stage 1 → 2: Loyal Member → Opportunity Detected

**Conversation Scenario 1.1: Expressing Financial Goals**
```
User: "I've been saving consistently for the past few months. What are some good options to grow my savings?"

Expected AI Response: Acknowledges savings pattern, introduces investment concepts
```

**Conversation Scenario 1.2: Showing Investment Interest**
```
User: "I keep hearing about mutual funds. Are they safe for someone like me?"

Expected AI Response: Explains mutual funds, builds confidence, mentions SIP benefits
```

**Conversation Scenario 1.3: Asking About Returns**
```
User: "My savings account gives me 3% interest. Can I get better returns somewhere else?"

Expected AI Response: Compares savings vs investment options, introduces risk-adjusted returns
```

**Expected Stage Transition:** After 1-2 conversations expressing investment interest, system should detect "Opportunity Detected"

---

### Stage 2 → 3: Opportunity Detected → Consideration

**Conversation Scenario 2.1: Understanding Investment Options**
```
User: "Tell me more about SIP. How does it work exactly?"

Expected AI Response: Explains SIP mechanism, rupee cost averaging, examples
```

**Conversation Scenario 2.2: Risk Assessment**
```
User: "What if the market crashes? Will I lose all my money in mutual funds?"

Expected AI Response: Addresses risk concerns, explains long-term investing, diversification
```

**Conversation Scenario 2.3: Amount Discussion**
```
User: "I can save about 5000 rupees per month. Is that enough to start investing?"

Expected AI Response: Confirms amount is sufficient, shows potential growth, encourages starting
```

**Conversation Scenario 2.4: Seeking Guidance**
```
User: "Which mutual fund should I choose? There are so many options."

Expected AI Response: Offers to schedule advisor consultation, provides basic fund categories
```

**Expected Stage Transition:** After discussing specifics and showing clear consideration, move to "Consideration"

---

### Stage 3 → 4: Consideration → Multi-Product Member

**Conversation Scenario 3.1: Ready to Start**
```
User: "I think I'm ready to start. What's the next step?"

Expected AI Response: Guides through account opening, KYC process, first SIP setup
```

**Conversation Scenario 3.2: Making First Investment**
```
User: "I want to start with a balanced fund, 5000 per month. Can you help me set this up?"

Expected AI Response: Confirms selection, initiates setup process, sets expectations
```

**Conversation Scenario 3.3: Confirmation Follow-up**
```
User: "My first SIP installment went through! When will I see returns?"

Expected AI Response: Celebrates milestone, sets realistic expectations, encourages patience
```

**Expected Stage Transition:** After completing first investment/SIP setup, move to "Multi-Product Member"

---

### NEGATIVE CASE: High-Value Member at Risk (Retention Mission)

**Scenario Overview:** After becoming a Multi-Product Member, Rohan experiences issues with fees or services, triggering a transition to the "High-Value Retention" mission with "At Risk" status. This tests the system's ability to detect churn signals and respond with retention strategies.

**Mission Switch:** Investment Product Adoption → High-Value Retention

**Journey Stages for Retention Mission:**
1. Active Member
2. 🚨 At Risk (Target State)
3. 🔄 Re-engagement
4. 💚 Retained Member

---

### NEGATIVE Stage 1: Multi-Product Member → At Risk

**Conversation Scenario N1.1: Fee Concerns**
```
User: "I just noticed the account maintenance fees are quite high. Why am I being charged so much?"

Expected AI Response: Acknowledges concern, explains fee structure, shows empathy
Expected Mission Status: Should detect dissatisfaction signal → High-Value Retention mission becomes priority
```

**Conversation Scenario N1.2: Competitor Comparison**
```
User: "I saw that other banks are offering zero maintenance fees. I'm thinking of switching."

Expected AI Response: Addresses concern proactively, offers retention solutions, emphasizes value
Expected Mission Status: Should detect churn risk → Stage moves to "At Risk"
```

**Conversation Scenario N1.3: Service Dissatisfaction**
```
User: "The customer service has been really slow lately. I've been on hold for 30 minutes."

Expected AI Response: Apologizes, offers immediate resolution, escalates if needed
Expected Mission Status: Confirms "At Risk" stage with multiple negative signals
```

**Conversation Scenario N1.4: Account Reduction Intent**
```
User: "I'm considering moving most of my funds to another bank. What do you have to say about that?"

Expected AI Response: Takes churn signal seriously, offers personalized retention package, requests opportunity to make things right
Expected Mission Status: Priority Mission = "High-Value Retention", Stage = "At Risk"
```

**Expected Stage Transition:** After 2-3 conversations expressing dissatisfaction, fees complaints, or competitor interest, system should:
- Switch priority mission to "High-Value Retention"
- Update stage to "At Risk"
- Wyzion analysis should show churn probability percentage
- Recommendation should focus on retention actions (fee waiver, relationship manager call, etc.)

**Interaction Signals to Add:**
```json
{
  "type": "negative_feedback",
  "signal": "warning",
  "title": "Multiple Fee Complaints",
  "description": "Member expressed dissatisfaction with account maintenance fees"
}
```

---

### RECOVERY Stage 2: At Risk → Re-engagement

**Conversation Scenario R1.1: Retention Offer Presented**
```
User: "What can you do to keep me as a customer? I need a better deal."

Expected AI Response: Presents personalized retention offer (fee waiver, upgraded account benefits, relationship manager assignment)
Expected Mission Status: Stage should move to "Re-engagement"
```

**Conversation Scenario R1.2: Addressing Concerns**
```
User: "If you waive the fees for 12 months, I'll consider staying."

Expected AI Response: Confirms ability to waive fees, explains value-added services, rebuilds trust
Expected Mission Status: Confirms "Re-engagement" with positive signal
```

**Conversation Scenario R1.3: Relationship Building**
```
User: "Tell me more about the premium account benefits you mentioned."

Expected AI Response: Details exclusive benefits (priority support, no ATM fees, higher interest rates, dedicated advisor), shows renewed value
Expected Mission Status: Continues "Re-engagement" with increasing engagement signals
```

**Expected Stage Transition:** After showing interest in retention offers and responding positively, move to "Re-engagement"

**Interaction Signals to Add:**
```json
{
  "type": "retention_engagement",
  "signal": "positive",
  "title": "Retention Offer Accepted",
  "description": "Member responded positively to fee waiver and premium benefits"
}
```

---

### RECOVERY Stage 3: Re-engagement → Retained Member

**Conversation Scenario R2.1: Acceptance of Retention Offer**
```
User: "Okay, that sounds fair. Let's upgrade my account to premium with the fee waiver."

Expected AI Response: Celebrates decision, confirms upgrade process, sets expectations for improved experience
Expected Mission Status: Stage should move toward "Retained Member"
```

**Conversation Scenario R2.2: Renewed Satisfaction**
```
User: "Thanks for working with me on this. I appreciate the effort to keep me as a customer."

Expected AI Response: Thanks member for giving another chance, reinforces commitment to excellent service
Expected Mission Status: Confirms "Retained Member" status
```

**Conversation Scenario R2.3: Continued Engagement**
```
User: "The premium account is much better. I'm glad I stayed."

Expected AI Response: Celebrates positive feedback, encourages continued engagement, offers additional services
Expected Mission Status: Solid "Retained Member", may switch back to "Investment Product Adoption" if stable
```

**Conversation Scenario R2.4: Return to Normal**
```
User: "Now that my account is sorted, I'd like to increase my SIP amount to 8000 per month."

Expected AI Response: Acknowledges stability, helps with SIP increase, shows continued investment support
Expected Mission Status: Should detect return to growth mindset
Expected Mission Switch: High-Value Retention → Investment Product Adoption (back to normal)
```

**Expected Stage Transition:** After accepting retention offer and expressing renewed satisfaction:
- Stage moves to "Retained Member"
- Churn probability drops significantly in Wyzion analysis
- Priority mission may switch back to "Investment Product Adoption" if member shows growth signals
- Recommendation should shift from retention to growth/expansion

**Interaction Signals to Add:**
```json
{
  "type": "retention_success",
  "signal": "positive",
  "title": "Premium Account Upgrade Completed",
  "description": "Member upgraded to premium account with fee waiver, expressing renewed satisfaction"
}
```

---

### NEGATIVE CASE TESTING CHECKLIST

**Pre-Test Setup:**
- [ ] Ensure Rohan (M001) is at "Multi-Product Member" stage in Investment Product Adoption mission
- [ ] Clear any existing "At Risk" interaction signals
- [ ] Verify both missions are configured in sample_missions()

**Test Steps:**
1. [ ] Start negative conversation expressing fee concerns
2. [ ] Send 2-3 messages expressing dissatisfaction or competitor interest
3. [ ] Click "🔄 Refresh Intent" after each negative conversation
4. [ ] Verify mission switches to "High-Value Retention"
5. [ ] Verify stage shows "At Risk" in journey progress
6. [ ] Check Wyzion analysis shows "churn probability" percentage
7. [ ] Verify recommendation includes retention actions (fee waiver, relationship call)
8. [ ] Start recovery conversation with retention offer discussion
9. [ ] Send 2-3 messages showing interest in staying/accepting offers
10. [ ] Click "🔄 Refresh Intent" and verify stage moves to "Re-engagement"
11. [ ] Send confirmation of accepting retention offer
12. [ ] Click "🔄 Refresh Intent" and verify stage moves to "Retained Member"
13. [ ] Send growth-minded message (increase SIP, etc.)
14. [ ] Click "🔄 Refresh Intent" and verify mission switches back to "Investment Product Adoption"

**Expected System Behavior:**
- ✅ AI detects negative sentiment from fee complaints and competitor mentions
- ✅ Priority mission automatically switches from Investment to Retention
- ✅ Stage progresses: Active Member → At Risk → Re-engagement → Retained Member
- ✅ Wyzion analysis reflects churn risk with percentage
- ✅ Recommendations shift from growth to retention and back to growth
- ✅ Interaction signals panel shows negative → warning → positive signals
- ✅ Mission switches back to Investment Product Adoption after stability

**Validation Points:**
- **At Risk Stage:** Wyzion should show "churn probability: 65-75%" and recommend "Schedule retention call" or "Waive account fees"
- **Re-engagement Stage:** Wyzion should show "churn probability: 35-45%" and recommend "Complete premium upgrade" or "Confirm retention offer"
- **Retained Member Stage:** Wyzion should show "churn probability: 10-15%" and recommend "Monitor satisfaction" or "Explore growth opportunities"
- **Return to Normal:** Mission switches back, recommendations focus on investment growth

---

### COMPLETE ROHAN JOURNEY: END-TO-END TEST SCENARIO

**Full Journey Test (30-40 minutes):**

This comprehensive scenario tests the complete journey including positive flow, negative disruption, and recovery.

**Phase 1: Positive Investment Journey (10-15 min)**
1. Loyal Member → Opportunity Detected (2-3 conversations about savings and investment interest)
2. Opportunity Detected → Consideration (2-3 conversations about SIP, risks, amounts)
3. Consideration → Multi-Product Member (1-2 conversations confirming readiness and first investment)

**Phase 2: Negative Disruption - At Risk (5-10 min)**
4. Multi-Product Member → At Risk (2-3 negative conversations about fees, competitors, dissatisfaction)
5. Verify mission switch to High-Value Retention
6. Verify Wyzion shows high churn probability and retention recommendations

**Phase 3: Recovery - Re-engagement (5-10 min)**
7. At Risk → Re-engagement (2-3 conversations showing interest in retention offers)
8. Verify stage progression and engagement signals

**Phase 4: Full Recovery - Return to Normal (5-10 min)**
9. Re-engagement → Retained Member (1-2 conversations accepting offers and expressing satisfaction)
10. Retained Member → Back to Investment Growth (1-2 conversations showing growth mindset)
11. Verify mission switches back to Investment Product Adoption
12. Verify recommendations shift from retention to growth

**Expected Total Conversations:** 15-20 messages
**Expected Mission Switches:** 2 (Investment → Retention → Investment)
**Expected Stage Transitions:** 7 stages total

---

## Member 2: Mr. Sharma (M002) - Healthcare Vertical

**Current Profile:**
- Vertical: Healthcare
- Persona: Chronic Care Patient
- Current Stage: Stable Patient
- Goal: Adopt a personalized, preventative wellness plan
- Age: 58
- Current Products: Primary Care, Cardiology
- Visit Frequency: Reactive

**Journey Stages:**
1. ✅ Stable Patient (Current)
2. ⚠️ Proactive Opportunity
3. 💬 Engagement
4. ❤️ Deepened Relationship

---

### Stage 1 → 2: Stable Patient → Proactive Opportunity

**Conversation Scenario 1.1: Health Status Inquiry**
```
User: "My recent checkup showed slightly elevated blood pressure. Should I be worried?"

Expected AI Response: Addresses concern, explains preventative measures, introduces wellness concepts
```

**Conversation Scenario 1.2: Lifestyle Questions**
```
User: "I've gained some weight recently. What can I do about it?"

Expected AI Response: Offers lifestyle recommendations, mentions cardiac wellness program relevance
```

**Conversation Scenario 1.3: Prevention Interest**
```
User: "How can I avoid heart problems in the future? I want to be proactive."

Expected AI Response: Recognizes proactive mindset, introduces preventative wellness programs
```

**Expected Stage Transition:** System detects proactive health interest, moves to "Proactive Opportunity"

---

### Stage 2 → 3: Proactive Opportunity → Engagement

**Conversation Scenario 2.1: Program Inquiry**
```
User: "Tell me about the cardiac wellness program. What does it include?"

Expected AI Response: Details program components: diet, exercise, monitoring, regular check-ins
```

**Conversation Scenario 2.2: Personalization Questions**
```
User: "Will the program be customized for my age and current health condition?"

Expected AI Response: Confirms personalization, explains assessment process, addresses specific needs
```

**Conversation Scenario 2.3: Commitment Exploration**
```
User: "How much time would I need to commit to this program?"

Expected AI Response: Outlines time commitment, flexibility options, emphasizes gradual approach
```

**Conversation Scenario 2.4: Benefits Discussion**
```
User: "What results can I expect if I follow the program?"

Expected AI Response: Sets realistic expectations, shares success metrics, emphasizes long-term benefits
```

**Expected Stage Transition:** After showing clear interest and asking specific questions, move to "Engagement"

---

### Stage 3 → 4: Engagement → Deepened Relationship

**Conversation Scenario 3.1: Enrollment Decision**
```
User: "I'd like to enroll in the cardiac wellness program. How do I start?"

Expected AI Response: Celebrates decision, schedules initial assessment, explains onboarding process
```

**Conversation Scenario 3.2: First Steps Taken**
```
User: "I've started following the diet plan you gave me. What else should I focus on?"

Expected AI Response: Acknowledges progress, introduces next wellness pillar, maintains encouragement
```

**Conversation Scenario 3.3: Progress Check-in**
```
User: "I've been walking 30 minutes daily for 2 weeks now. My BP seems better!"

Expected AI Response: Celebrates milestone, reinforces positive behavior, suggests continued monitoring
```

**Conversation Scenario 3.4: Long-term Commitment**
```
User: "This program is really helping me. Can I continue this long-term?"

Expected AI Response: Confirms ongoing support, introduces advanced wellness options, deepens relationship
```

**Expected Stage Transition:** After active participation and commitment to wellness plan, move to "Deepened Relationship"

---

## Member 3: Priya K. (M003) - E-commerce Vertical

**Current Profile:**
- Vertical: E-commerce
- Persona: New Website Visitor
- Current Stage: Prospect
- Goal: Convert into a high-value first-time customer
- Age: 35
- Session Count: 2
- Browsing Behavior: High-intent

**Journey Stages:**
1. 🚶 Prospect (Current)
2. 🎯 Qualified Lead
3. 📅 Consultation Booked
4. 🛍️ First Purchase

---

### Stage 1 → 2: Prospect → Qualified Lead

**Conversation Scenario 1.1: Product Interest**
```
User: "I'm looking for a premium handbag for work. What options do you have?"

Expected AI Response: Acknowledges need, asks preferences (style, budget, occasion), shows relevant options
```

**Conversation Scenario 1.2: Specific Requirements**
```
User: "I need something professional but stylish, budget around 40-50k. What would you recommend?"

Expected AI Response: Recognizes budget tier (high-value), shows curated premium selections
```

**Conversation Scenario 1.3: Product Details**
```
User: "Tell me more about this Italian leather tote. Is it worth the price?"

Expected AI Response: Provides detailed info on quality, craftsmanship, value proposition
```

**Conversation Scenario 1.4: Comparison Shopping**
```
User: "I'm comparing this with another brand. What makes yours special?"

Expected AI Response: Highlights unique selling points, offers personalized guidance
```

**Expected Stage Transition:** After showing clear intent with budget and specific requirements, move to "Qualified Lead"

---

### Stage 2 → 3: Qualified Lead → Consultation Booked

**Conversation Scenario 2.1: Seeking Expert Advice**
```
User: "I'm torn between two styles. Can someone help me choose what suits me better?"

Expected AI Response: Offers personal styling consultation, explains benefits of 1-on-1 guidance
```

**Conversation Scenario 2.2: Size/Fit Concerns**
```
User: "I'm not sure about the size. I don't want to order the wrong one."

Expected AI Response: Addresses concern, offers virtual consultation to ensure perfect fit
```

**Conversation Scenario 2.3: Customization Interest**
```
User: "Can I get this bag personalized with my initials?"

Expected AI Response: Confirms customization options, suggests consultation to finalize details
```

**Conversation Scenario 2.4: Ready for Guidance**
```
User: "This is a big purchase for me. Can I speak to a stylist before deciding?"

Expected AI Response: Schedules video/phone consultation, confirms time slot, sets expectations
```

**Expected Stage Transition:** After booking consultation or requesting expert guidance, move to "Consultation Booked"

---

### Stage 3 → 4: Consultation Booked → First Purchase

**Conversation Scenario 3.1: Post-Consultation Confidence**
```
User: "Thanks for the consultation! The stylist helped me narrow it down to the perfect bag."

Expected AI Response: Follows up, offers to complete purchase, provides checkout assistance
```

**Conversation Scenario 3.2: Ready to Buy**
```
User: "I'd like to order the brown leather tote we discussed, with monogramming."

Expected AI Response: Confirms selection, guides through checkout, explains delivery timeline
```

**Conversation Scenario 3.3: Purchase Assurance**
```
User: "What's your return policy if it doesn't work out?"

Expected AI Response: Explains hassle-free returns, provides confidence, removes purchase barrier
```

**Conversation Scenario 3.4: Completing Transaction**
```
User: "Okay, I'm ready to check out. Can you help me apply any first-time buyer offers?"

Expected AI Response: Applies available discounts, completes transaction, celebrates first purchase
```

**Conversation Scenario 3.5: Order Confirmation**
```
User: "My order went through! When will it arrive?"

Expected AI Response: Confirms order, provides tracking info, sets delivery expectations, thanks for purchase
```

**Expected Stage Transition:** After completing first purchase, move to "First Purchase"

---

## Testing Guidelines

### How to Test

1. **Select the member** from the dropdown in the UI
2. **Start with Stage 1 scenarios** and progress sequentially
3. **Wait for AI response** after each message
4. **Click "Refresh Intent"** button after 2-3 conversations to see if stage has changed
5. **Progress to next stage scenarios** once transition occurs

### Expected Behavior

- **Automatic Stage Detection**: The AI should analyze conversation history and detect when member has progressed
- **Intent Panel Update**: After clicking "Refresh Intent", the journey progress should show updated stage
- **Natural Progression**: Stages should update after 2-4 relevant conversations for each transition
- **Memory Retention**: AI should remember previous conversations and reference them naturally

### Validation Checklist

For each member, verify:
- ✅ Stage transitions occur after appropriate conversations
- ✅ Journey progress visualization updates correctly
- ✅ AI responses reference conversation history
- ✅ Insight Detail View reflects current stage and analysis
- ✅ Member dropdown shows correct name and vertical only (no persona)

---

## Quick Test Script

### 5-Minute Quick Test (One Member)

**For Rohan S. (BFSI):**
1. Select "Rohan S. - BFSI" from dropdown
2. Type: "I've been saving consistently. What are some good options to grow my savings?"
3. Wait for response, then type: "Tell me more about SIP. How does it work?"
4. Click "🔄 Refresh Intent" - Should show "Opportunity Detected" or "Consideration"
5. Type: "I think I'm ready to start. What's the next step?"
6. Click "🔄 Refresh Intent" - Should show later stage

### 15-Minute Full Test (All Members)

Run quick test for each member:
- Rohan S. (BFSI) - Investment progression
- Mr. Sharma (Healthcare) - Wellness program progression
- Priya K. (E-commerce) - Purchase journey progression

---

## Notes

- Conversations should feel natural and member-specific
- AI should adapt tone based on vertical (professional for BFSI, caring for Healthcare, friendly for E-commerce)
- Stage transitions may take 2-4 relevant conversations
- Manual "Refresh Intent" click required to see stage updates in UI
- Memory system ensures AI remembers all previous interactions

