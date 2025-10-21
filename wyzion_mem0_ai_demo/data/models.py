from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ============================================================================
# DATA MODELS
# ============================================================================


@dataclass
class Vertical:
    vertical: str
    use_case: str
    description: str


@dataclass
class JourneyStage:
    stage: str
    emoji: str
    color: str
    vertical: str


@dataclass
class Mission:
    mission_id: str
    vertical: str
    title: str
    description: str
    type: str
    stages: List[str]
    end_goal: str


@dataclass
class Member:
    id: str
    name: str
    persona: str
    vertical: str
    age: int
    joined_year: int
    current_stage: str
    goal: str
    risk_level: str
    # Optional domain-specific fields
    credit_score: Optional[int] = None
    transaction_volume: Optional[float] = None
    current_products: Optional[List[str]] = field(default_factory=list)
    visit_frequency: Optional[str] = None
    session_count: Optional[int] = None
    browsing_behavior: Optional[str] = None


@dataclass
class Interaction:
    user_id: str
    vertical: str
    type: str
    icon: str
    title: str
    description: str
    timestamp: str
    signal: str
    journey_stage: str
    next_action: str


@dataclass
class JourneyProgress:
    member: Member
    mission: Mission
    current_stage: str
    interactions_count: int
    recent_interactions: List[Interaction]
    next_stage: str


# ============================================================================
# SAMPLE DATA DEFINITIONS
# ============================================================================


def get_verticals() -> List[Vertical]:
    """Define the different verticals with their use cases"""
    return [
        Vertical(
            "BFSI",
            "Deepening Relationship",
            "Nurture a hesitant but high-potential saver into a confident, multi-product investor over multiple, trust-building interactions",
        ),
        Vertical(
            "Healthcare",
            "Proactive Deepening",
            "Use historical data and proactive timing to move a patient from reactive care to a personalized, preventative wellness journey",
        ),
        Vertical(
            "E-commerce",
            "Proactive Acquisition",
            "Identify an anonymous, casual browser as a high-value prospect over two sessions, orchestrating a premium, human-led sales experience",
        ),
    ]


def get_journey_stages() -> List[JourneyStage]:
    """Define all journey stages across verticals"""
    return [
        # BFSI
        JourneyStage("Loyal Member", "✅", "green", "BFSI"),
        JourneyStage("Opportunity Detected", "⚠️", "yellow", "BFSI"),
        JourneyStage("Consideration", "🤔", "blue", "BFSI"),
        JourneyStage("Multi-Product Member", "🌟", "gold", "BFSI"),
        # Healthcare
        JourneyStage("Stable Patient", "✅", "green", "Healthcare"),
        JourneyStage("Proactive Opportunity", "⚠️", "yellow", "Healthcare"),
        JourneyStage("Engagement", "💬", "blue", "Healthcare"),
        JourneyStage("Deepened Relationship", "❤️", "red", "Healthcare"),
        # E-commerce
        JourneyStage("Prospect", "🚶", "gray", "E-commerce"),
        JourneyStage("Qualified Lead", "🎯", "orange", "E-commerce"),
        JourneyStage("Consultation Booked", "📅", "blue", "E-commerce"),
        JourneyStage("First Purchase", "🛍️", "purple", "E-commerce"),
    ]


def get_stages_by_vertical(vertical: str) -> List[JourneyStage]:
    """Get stages by vertical"""
    return [s for s in get_journey_stages() if s.vertical.lower() == vertical.lower()]


def sample_members() -> List[Member]:
    """Return sample members with enhanced profile data"""
    return [
        Member(
            id="M001",
            name="Rohan S.",
            persona="Existing Loyal Member",
            vertical="BFSI",
            age=30,
            joined_year=2018,
            credit_score=720,
            transaction_volume=25000,
            current_products=["Checking Account", "Savings Account"],
            current_stage="Loyal Member",
            goal="Adopt a new investment product (Mutual Fund SIP)",
            risk_level="low",
        ),
        Member(
            id="M002",
            name="Mr. Sharma",
            persona="Chronic Care Patient",
            vertical="Healthcare",
            age=58,
            joined_year=2020,
            current_products=["Primary Care", "Cardiology"],
            visit_frequency="reactive",
            current_stage="Stable Patient",
            goal="Adopt a personalized, preventative wellness plan",
            risk_level="medium",
        ),
        Member(
            id="M003",
            name="Priya K.",
            persona="New Website Visitor",
            vertical="E-commerce",
            age=35,
            joined_year=2024,
            session_count=2,
            browsing_behavior="high-intent",
            current_stage="Prospect",
            goal="Convert into a high-value first-time customer",
            risk_level="low",
        ),
    ]


def sample_missions() -> List[Mission]:
    """Define missions aligned with the blueprint journeys"""
    return [
        Mission(
            "MSN001",
            "BFSI",
            "Investment Product Adoption",
            "Guide loyal member to adopt Mutual Fund SIP",
            "deepening_relationship",
            ["Loyal Member", "Opportunity Detected", "Consideration", "Multi-Product Member"],
            "Adopt new investment product (Mutual Fund SIP)",
        ),
        Mission(
            "MSN002",
            "Healthcare",
            "Preventative Wellness Journey",
            "Transition chronic care patient to proactive wellness",
            "proactive_deepening",
            ["Stable Patient", "Proactive Opportunity", "Engagement", "Deepened Relationship"],
            "Adopt a personalized, preventative wellness plan",
        ),
        Mission(
            "MSN003",
            "E-commerce",
            "Premium Customer Acquisition",
            "Convert anonymous browser to first-time buyer",
            "proactive_acquisition",
            ["Prospect", "Qualified Lead", "Consultation Booked", "First Purchase"],
            "Convert into a high-value first-time customer",
        ),
    ]


def sample_interactions() -> List[Interaction]:
    """Return sample member interactions and signals aligned with journeys"""
    now = datetime.now()
    data = []

    def ts(days=0, hours=0):
        return (now - timedelta(days=days, hours=hours)).strftime("%B %d, %I:%M %p")

    # --- BFSI ---
    data.extend(
        [
            Interaction(
                "M001",
                "BFSI",
                "account_activity",
                "✅",
                "Consistent Savings Pattern Detected",
                "Member has maintained consistent monthly savings of ₹15,000+ for 6 months.",
                ts(days=1),
                "positive",
                "Loyal Member",
                "Identify investment opportunity",
            ),
            Interaction(
                "M001",
                "BFSI",
                "behavior_signal",
                "⚠️",
                "Investment Content Engagement",
                "Viewed 'Mutual Fund Basics' and SIP calculator.",
                ts(hours=18),
                "positive",
                "Opportunity Detected",
                "Send personalized investment guide",
            ),
            Interaction(
                "M001",
                "BFSI",
                "engagement",
                "🤔",
                "Investment Webinar Registration",
                "Registered for 'Smart Investing for Beginners' webinar.",
                ts(hours=5),
                "positive",
                "Consideration",
                "Schedule advisor consultation",
            ),
        ]
    )

    # --- Healthcare ---
    data.extend(
        [
            Interaction(
                "M002",
                "Healthcare",
                "health_data",
                "✅",
                "Recent Checkup Completed",
                "Blood pressure slightly elevated, weight up 5 lbs.",
                ts(days=3),
                "neutral",
                "Stable Patient",
                "Analyze preventative opportunities",
            ),
            Interaction(
                "M002",
                "Healthcare",
                "proactive_trigger",
                "⚠️",
                "Preventative Care Opportunity Identified",
                "Ideal candidate for cardiac wellness program.",
                ts(days=2),
                "positive",
                "Proactive Opportunity",
                "Send personalized wellness plan",
            ),
            Interaction(
                "M002",
                "Healthcare",
                "engagement",
                "💬",
                "Wellness Program Email Opened",
                "Clicked 'Learn More' on cardiac wellness email.",
                ts(hours=8),
                "positive",
                "Engagement",
                "Schedule consultation call",
            ),
        ]
    )

    # --- E-commerce ---
    data.extend(
        [
            Interaction(
                "M003",
                "E-commerce",
                "browsing",
                "🚶",
                "First Visit - Premium Category",
                "Browsed luxury handbags for 8 minutes, viewed 5 products.",
                ts(days=2),
                "neutral",
                "Prospect",
                "Track return visit",
            ),
            Interaction(
                "M003",
                "E-commerce",
                "intent_signal",
                "🎯",
                "Return Visit - High Intent Behavior",
                "Added ₹45,000 handbag to cart and checked size guide.",
                ts(hours=6),
                "positive",
                "Qualified Lead",
                "Offer personal shopping consultation",
            ),
            Interaction(
                "M003",
                "E-commerce",
                "engagement",
                "📅",
                "Virtual Consultation Scheduled",
                "Booked 30-min video consultation with style advisor.",
                ts(hours=2),
                "positive",
                "Consultation Booked",
                "Prepare personalized recommendations",
            ),
        ]
    )

    return data


# ============================================================================
# COMPUTATION FUNCTIONS
# ============================================================================


def get_member_interactions(user_id: str) -> List[Interaction]:
    return [i for i in sample_interactions() if i.user_id == user_id]


def get_member_journey_progress(user_id: str) -> JourneyProgress:
    members = sample_members()
    missions = sample_missions()

    member = next(m for m in members if m.id == user_id)
    mission = next(m for m in missions if m.vertical == member.vertical)
    interactions = get_member_interactions(user_id)

    next_stage = "Journey Complete"
    if member.current_stage in mission.stages:
        idx = mission.stages.index(member.current_stage)
        if idx < len(mission.stages) - 1:
            next_stage = mission.stages[idx + 1]

    return JourneyProgress(
        member=member,
        mission=mission,
        current_stage=member.current_stage,
        interactions_count=len(interactions),
        recent_interactions=interactions[:3],
        next_stage=next_stage,
    )


def get_all_journeys_summary() -> List[Dict]:
    """Get summary of all member journeys"""
    members = sample_members()
    summary = []
    for member in members:
        progress = get_member_journey_progress(member.id)
        summary.append(
            {
                "member_name": member.name,
                "vertical": member.vertical,
                "current_stage": progress.current_stage,
                "next_stage": progress.next_stage,
                "interactions": progress.interactions_count,
            }
        )
    return summary
