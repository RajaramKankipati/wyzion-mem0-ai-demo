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
    ]


def get_journey_stages() -> List[JourneyStage]:
    """Define all journey stages across verticals"""
    return [
        # BFSI - Investment Product Adoption
        JourneyStage("Loyal Member", "✅", "green", "BFSI"),
        JourneyStage("Opportunity Detected", "⚠️", "yellow", "BFSI"),
        JourneyStage("Consideration", "🤔", "blue", "BFSI"),
        JourneyStage("Multi-Product Member", "🌟", "gold", "BFSI"),
        # BFSI - Churn Reduction
        JourneyStage("Active Member", "✅", "green", "BFSI"),
        JourneyStage("At Risk", "🚨", "red", "BFSI"),
        JourneyStage("Re-engagement", "🔄", "orange", "BFSI"),
        JourneyStage("Retained Member", "💚", "green", "BFSI"),
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
        )
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
            "BFSI",
            "High-Value Retention",
            "Identify and re-engage at-risk members to prevent churn",
            "retention",
            ["Active Member", "At Risk", "Re-engagement", "Retained Member"],
            "Retain at-risk member and restore active engagement",
        ),
    ]


def sample_interactions() -> List[Interaction]:
    """Return sample member interactions and signals aligned with journeys"""
    now = datetime.now()
    data = []

    def ts(days=0, hours=0):
        return (now - timedelta(days=days, hours=hours)).strftime("%B %d, %I:%M %p")

    # --- BFSI - Investment Product Adoption (Rohan) ---
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
            # OPTIONAL: Uncomment below for negative test case scenario (At Risk)
            # These interactions simulate churn signals that trigger High-Value Retention mission
            # Interaction(
            #     "M001",
            #     "BFSI",
            #     "negative_feedback",
            #     "🚨",
            #     "Multiple Fee Complaints",
            #     "Member expressed dissatisfaction with account maintenance fees and compared with competitor offerings.",
            #     ts(hours=2),
            #     "warning",
            #     "At Risk",
            #     "Schedule retention call",
            # ),
            # Interaction(
            #     "M001",
            #     "BFSI",
            #     "competitor_signal",
            #     "⚠️",
            #     "Competitor Comparison Detected",
            #     "Member mentioned considering switching to another bank with zero fees.",
            #     ts(hours=1),
            #     "negative",
            #     "At Risk",
            #     "Present retention offer",
            # ),
            # Interaction(
            #     "M001",
            #     "BFSI",
            #     "service_complaint",
            #     "❌",
            #     "Service Quality Concern",
            #     "Member reported long wait times and poor customer service experience.",
            #     ts(minutes=30),
            #     "negative",
            #     "At Risk",
            #     "Escalate to relationship manager",
            # ),
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
