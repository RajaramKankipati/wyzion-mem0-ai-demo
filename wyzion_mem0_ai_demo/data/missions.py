from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

# ============================================================================
# VERTICAL DEFINITIONS
# ============================================================================


def get_verticals():
    """Define the different verticals with their use cases"""
    return [
        {
            "vertical": "BFSI",
            "use_case": "Deepening Relationship",
            "description": "Nurture a hesitant but high-potential saver into a confident, multi-product investor over multiple, trust-building interactions",
        },
        {
            "vertical": "Healthcare",
            "use_case": "Proactive Deepening",
            "description": "Use historical data and proactive timing to move a patient from reactive care to a personalized, preventative wellness journey",
        },
        {
            "vertical": "E-commerce",
            "use_case": "Proactive Acquisition",
            "description": "Identify an anonymous, casual browser as a high-value prospect over two sessions, orchestrating a premium, human-led sales experience",
        },
    ]


# ============================================================================
# JOURNEY STAGE DEFINITIONS
# ============================================================================


class JourneyStage:
    """Defines the possible journey stages with emojis"""

    # BFSI Stages
    LOYAL_MEMBER = {"stage": "Loyal Member", "emoji": "✅", "color": "green"}
    OPPORTUNITY_DETECTED = {"stage": "Opportunity Detected", "emoji": "⚠️", "color": "yellow"}
    CONSIDERATION = {"stage": "Consideration", "emoji": "🤔", "color": "blue"}
    MULTI_PRODUCT_MEMBER = {"stage": "Multi-Product Member", "emoji": "🌟", "color": "gold"}

    # Healthcare Stages
    STABLE_PATIENT = {"stage": "Stable Patient", "emoji": "✅", "color": "green"}
    PROACTIVE_OPPORTUNITY = {"stage": "Proactive Opportunity", "emoji": "⚠️", "color": "yellow"}
    ENGAGEMENT = {"stage": "Engagement", "emoji": "💬", "color": "blue"}
    DEEPENED_RELATIONSHIP = {"stage": "Deepened Relationship", "emoji": "❤️", "color": "red"}

    # E-commerce Stages
    PROSPECT = {"stage": "Prospect", "emoji": "🚶", "color": "gray"}
    QUALIFIED_LEAD = {"stage": "Qualified Lead", "emoji": "🎯", "color": "orange"}
    CONSULTATION_BOOKED = {"stage": "Consultation Booked", "emoji": "📅", "color": "blue"}
    FIRST_PURCHASE = {"stage": "First Purchase", "emoji": "🛍️", "color": "purple"}


# ============================================================================
# MEMBER/USER DATA
# ============================================================================


def sample_members():
    """Return sample members with enhanced profile data"""
    data = [
        {
            "id": "M001",
            "name": "Rohan S.",
            "persona": "Existing Loyal Member",
            "vertical": "BFSI",
            "age": 30,
            "joined_year": 2018,
            "credit_score": 720,
            "current_products": ["Checking Account", "Savings Account"],
            "transaction_volume": 25000,
            "current_stage": "Loyal Member",
            "goal": "Adopt a new investment product (Mutual Fund SIP)",
            "risk_level": "low",
        },
        {
            "id": "M002",
            "name": "Mr. Sharma",
            "persona": "Chronic Care Patient",
            "vertical": "Healthcare",
            "age": 58,
            "joined_year": 2020,
            "current_products": ["Primary Care", "Cardiology"],
            "visit_frequency": "reactive",
            "current_stage": "Stable Patient",
            "goal": "Adopt a personalized, preventative wellness plan",
            "risk_level": "medium",
        },
        {
            "id": "M003",
            "name": "Priya K.",
            "persona": "New Website Visitor",
            "vertical": "E-commerce",
            "age": 35,
            "joined_year": 2024,
            "session_count": 2,
            "browsing_behavior": "high-intent",
            "current_stage": "Prospect",
            "goal": "Convert into a high-value first-time customer",
            "risk_level": "low",
        },
    ]
    return pd.DataFrame(data)


# ============================================================================
# MISSION/JOURNEY DEFINITIONS
# ============================================================================


def sample_missions():
    """Define missions aligned with the blueprint journeys"""
    data = [
        {
            "mission_id": "MSN001",
            "vertical": "BFSI",
            "title": "Investment Product Adoption",
            "description": "Guide loyal member to adopt Mutual Fund SIP",
            "type": "deepening_relationship",
            "stages": ["Loyal Member", "Opportunity Detected", "Consideration", "Multi-Product Member"],
            "end_goal": "Adopt new investment product (Mutual Fund SIP)",
        },
        {
            "mission_id": "MSN002",
            "vertical": "Healthcare",
            "title": "Preventative Wellness Journey",
            "description": "Transition chronic care patient to proactive wellness",
            "type": "proactive_deepening",
            "stages": ["Stable Patient", "Proactive Opportunity", "Engagement", "Deepened Relationship"],
            "end_goal": "Adopt a personalized, preventative wellness plan",
        },
        {
            "mission_id": "MSN003",
            "vertical": "E-commerce",
            "title": "Premium Customer Acquisition",
            "description": "Convert anonymous browser to first-time buyer",
            "type": "proactive_acquisition",
            "stages": ["Prospect", "Qualified Lead", "Consultation Booked", "First Purchase"],
            "end_goal": "Convert into a high-value first-time customer",
        },
    ]
    return pd.DataFrame(data)


# ============================================================================
# INTERACTIONS & SIGNALS
# ============================================================================


def sample_interactions():
    """Return sample member interactions and signals aligned with journeys"""
    now = datetime.now()

    data = [
        # Rohan S. (M001) - BFSI: Deepening Relationship Journey
        {
            "user_id": "M001",
            "vertical": "BFSI",
            "type": "account_activity",
            "icon": "✅",
            "title": "Consistent Savings Pattern Detected",
            "description": "Member has maintained consistent monthly savings of ₹15,000+ for 6 months.",
            "timestamp": (now - timedelta(days=1)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Loyal Member",
            "next_action": "Identify investment opportunity",
        },
        {
            "user_id": "M001",
            "type": "behavior_signal",
            "icon": "⚠️",
            "title": "Investment Content Engagement",
            "description": "Member viewed 'Mutual Fund Basics' article and SIP calculator on mobile app.",
            "timestamp": (now - timedelta(hours=18)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Opportunity Detected",
            "next_action": "Send personalized investment guide",
        },
        {
            "user_id": "M001",
            "type": "engagement",
            "icon": "🤔",
            "title": "Investment Webinar Registration",
            "description": "Member registered for 'Smart Investing for Beginners' webinar next Tuesday.",
            "timestamp": (now - timedelta(hours=5)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Consideration",
            "next_action": "Schedule advisor consultation",
        },
        # Mr. Sharma (M002) - Healthcare: Proactive Deepening Journey
        {
            "user_id": "M002",
            "vertical": "Healthcare",
            "type": "health_data",
            "icon": "✅",
            "title": "Recent Checkup Completed",
            "description": "Annual physical completed. Blood pressure slightly elevated, weight up 5 lbs.",
            "timestamp": (now - timedelta(days=3)).strftime("%B %d, %I:%M %p"),
            "signal": "neutral",
            "journey_stage": "Stable Patient",
            "next_action": "Analyze preventative opportunities",
        },
        {
            "user_id": "M002",
            "type": "proactive_trigger",
            "icon": "⚠️",
            "title": "Preventative Care Opportunity Identified",
            "description": "Based on health trends, patient is ideal candidate for cardiac wellness program.",
            "timestamp": (now - timedelta(days=2)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Proactive Opportunity",
            "next_action": "Send personalized wellness plan",
        },
        {
            "user_id": "M002",
            "type": "engagement",
            "icon": "💬",
            "title": "Wellness Program Email Opened",
            "description": "Patient opened and clicked 'Learn More' on cardiac wellness program email.",
            "timestamp": (now - timedelta(hours=8)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Engagement",
            "next_action": "Schedule consultation call",
        },
        # Priya K. (M003) - E-commerce: Proactive Acquisition Journey
        {
            "user_id": "M003",
            "vertical": "E-commerce",
            "type": "browsing",
            "icon": "🚶",
            "title": "First Visit - Premium Category",
            "description": "New visitor browsed luxury handbag collection for 8 minutes, viewed 5 products.",
            "timestamp": (now - timedelta(days=2)).strftime("%B %d, %I:%M %p"),
            "signal": "neutral",
            "journey_stage": "Prospect",
            "next_action": "Track return visit",
        },
        {
            "user_id": "M003",
            "type": "intent_signal",
            "icon": "🎯",
            "title": "Return Visit - High Intent Behavior",
            "description": "Returned within 48hrs. Added ₹45,000 handbag to cart, read reviews, checked size guide.",
            "timestamp": (now - timedelta(hours=6)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Qualified Lead",
            "next_action": "Offer personal shopping consultation",
        },
        {
            "user_id": "M003",
            "type": "engagement",
            "icon": "📅",
            "title": "Virtual Consultation Scheduled",
            "description": "Visitor booked 30-min video consultation with luxury style advisor for tomorrow.",
            "timestamp": (now - timedelta(hours=2)).strftime("%B %d, %I:%M %p"),
            "signal": "positive",
            "journey_stage": "Consultation Booked",
            "next_action": "Prepare personalized recommendations",
        },
    ]

    return data


def get_member_interactions(user_id: str) -> List[Dict]:
    """Get interactions for a specific member"""
    all_interactions = sample_interactions()
    return [interaction for interaction in all_interactions if interaction["user_id"] == user_id]


def get_member_journey_progress(user_id: str) -> Dict:
    """Get the current journey progress for a member"""
    members_df = sample_members()
    missions_df = sample_missions()

    member = members_df[members_df["id"] == user_id].iloc[0]
    mission = missions_df[missions_df["vertical"] == member["vertical"]].iloc[0]
    interactions = get_member_interactions(user_id)

    return {
        "member": member.to_dict(),
        "mission": mission.to_dict(),
        "current_stage": member["current_stage"],
        "interactions_count": len(interactions),
        "recent_interactions": interactions[:3] if interactions else [],
        "next_stage": (
            mission["stages"][mission["stages"].index(member["current_stage"]) + 1]
            if member["current_stage"] in mission["stages"]
            and mission["stages"].index(member["current_stage"]) < len(mission["stages"]) - 1
            else "Journey Complete"
        ),
    }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_all_journeys_summary():
    """Get a summary of all active journeys"""
    members_df = sample_members()
    summary = []

    for _, member in members_df.iterrows():
        progress = get_member_journey_progress(member["id"])
        summary.append(
            {
                "member_name": member["name"],
                "vertical": member["vertical"],
                "current_stage": progress["current_stage"],
                "next_stage": progress["next_stage"],
                "interactions": progress["interactions_count"],
            }
        )

    return pd.DataFrame(summary)
