import json
import os
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from threading import Lock

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from openai import OpenAI

from wyzion_mem0_ai_demo.data.models import get_member_interactions, sample_members, sample_missions
from wyzion_mem0_ai_demo.helper.json_formatting import clean_text
from wyzion_mem0_ai_demo.tools.memory_tools import (
    add_member_facts,
    add_memory,
    get_all_memories,
    initialize_memory_client,
    search_memories,
)
from wyzion_mem0_ai_demo.tools.rag_system import get_rag_system, initialize_rag_system
from wyzion_mem0_ai_demo.utils.logger import configure_third_party_loggers, get_logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = get_logger(__name__)
configure_third_party_loggers()

# Thread pool for async memory operations
memory_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="memory_worker")


# --------------------------
# Local Memory Cache
# --------------------------
class LocalMemoryCache:
    """
    Thread-safe local cache for conversations before they're synced to Mem0.
    This ensures summaries and intents have access to the latest conversations
    even if Mem0 sync is still in progress.
    """

    def __init__(self):
        self._cache = defaultdict(list)  # user_id -> list of memory strings
        self._lock = Lock()
        logger.info("LocalMemoryCache initialized")

    def add(self, user_id: str, memory_text: str):
        """Add a memory to the cache for a specific user"""
        with self._lock:
            self._cache[user_id].append(memory_text)
            logger.debug(f"Added memory to cache for user_id={user_id}, total cached: {len(self._cache[user_id])}")

    def get(self, user_id: str):
        """Get all cached memories for a user"""
        with self._lock:
            memories = self._cache[user_id].copy()
            logger.debug(f"Retrieved {len(memories)} cached memories for user_id={user_id}")
            return memories

    def clear(self, user_id: str):
        """Clear all cached memories for a user (called after successful Mem0 sync)"""
        with self._lock:
            count = len(self._cache[user_id])
            self._cache[user_id].clear()
            logger.debug(f"Cleared {count} cached memories for user_id={user_id}")

    def get_all_users(self):
        """Get list of all user IDs with cached memories"""
        with self._lock:
            return list(self._cache.keys())


# Global memory cache instance
memory_cache = LocalMemoryCache()


# --------------------------
# Member Stage Tracking
# --------------------------
class MemberStageTracker:
    """
    Thread-safe tracker for member journey stages.
    Updates the current stage based on conversation intent detection.
    """

    def __init__(self):
        self._stages = {}  # user_id -> current_stage
        self._lock = Lock()
        logger.info("MemberStageTracker initialized")

    def update_stage(self, user_id: str, stage: str):
        """Update the current stage for a member"""
        with self._lock:
            old_stage = self._stages.get(user_id)
            self._stages[user_id] = stage
            logger.info(f"Updated stage for user_id={user_id}: {old_stage} -> {stage}")

    def get_stage(self, user_id: str, default_stage: str = ""):
        """Get the current stage for a member"""
        with self._lock:
            return self._stages.get(user_id, default_stage)

    def has_stage(self, user_id: str):
        """Check if a stage has been set for a member"""
        with self._lock:
            return user_id in self._stages


# Global stage tracker instance
stage_tracker = MemberStageTracker()


# --------------------------
# Helper functions
# --------------------------
def async_add_memory(messages_json: str, user_id: str):
    """
    Add memory asynchronously in the background without blocking the response.

    Strategy:
    1. Write to local cache immediately (instant, no blocking)
    2. Sync to Mem0 in background thread (3-4 seconds, async)
    3. Clear cache after successful Mem0 sync

    This ensures:
    - Instant response to users
    - Summaries/intents have access to latest conversations
    - Eventually consistent with Mem0 for persistence
    """
    # Parse messages to create human-readable memory text for cache
    try:
        message_list = json.loads(messages_json)
        # Create a summary of the conversation for the cache
        conversation_summary = ""
        for msg in message_list:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                conversation_summary += f"User asked: {content}\n"
            elif role == "assistant":
                conversation_summary += f"Assistant replied: {content}\n"

        # Add to local cache immediately (instant, non-blocking)
        memory_cache.add(user_id, conversation_summary.strip())
        logger.debug(f"Added conversation to local cache for user_id={user_id}")
    except Exception as e:
        logger.error(f"Error adding to local cache for user_id={user_id}: {e}", exc_info=True)

    # Background task to sync with Mem0
    def _add_memory_task():
        try:
            result = add_memory(messages_json, user_id)
            result_dict = json.loads(result)

            if result_dict.get("success"):
                logger.info(f"Async memory storage to Mem0 completed for user_id={user_id}")
                # Note: We don't clear cache here because Mem0 might have processed/summarized
                # the conversation differently. Cache will be used to supplement Mem0 data.
            else:
                logger.error(f"Mem0 storage failed for user_id={user_id}: {result_dict.get('error')}")

            return result
        except Exception as e:
            logger.error(f"Error in async memory storage for user_id={user_id}: {e}", exc_info=True)
            return json.dumps({"success": False, "error": str(e)})

    # Submit to thread pool and return immediately
    future = memory_executor.submit(_add_memory_task)
    logger.debug(f"Memory storage task submitted to background thread for user_id={user_id}")
    return future


# --------------------------
# AI Assistant Agent Class
# --------------------------
class BankingAssistant:
    def __init__(self):
        logger.info("Initializing BankingAssistant")
        try:
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
            raise

        try:
            # Initialize mem0 memory client for tools
            initialize_memory_client(api_key=os.environ.get("MEM0_API_KEY"))
            logger.info("Mem0 memory client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0 client: {e}", exc_info=True)
            raise

        try:
            # Initialize RAG system for knowledge base
            initialize_rag_system(self.client)
            logger.info("RAG system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}", exc_info=True)
            # Don't raise - app can still work without RAG

        self.system_message = (
            "You are a helpful AI Banking Assistant specialized in financial services and customer retention. "
            "When past conversation history is provided, seamlessly continue the conversation as if it's an ongoing dialogue. "
            "Reference previous discussions naturally, acknowledge the user's past questions and concerns, "
            "and build upon what was previously discussed without explicitly saying 'based on our previous conversation' unless contextually appropriate. "
            "Make the user feel understood and valued by demonstrating awareness of their financial journey. "
            "Provide personalized, helpful, professional, and accurate financial guidance that feels like a warm continuation of an existing relationship. "
            "When member-specific facts are available in the conversation history (such as name, age, persona, current stage, goals, credit score, transaction volume), "
            "use them naturally to provide personalized banking and financial advice. "
            "\n\nIMPORTANT: Keep responses brief and concise (2-3 sentences max). Provide quick, actionable insights."
        )
        logger.info("BankingAssistant initialized successfully")

    def initialize_member_facts_for_all(self):
        """Initialize member facts in memory for all members. This is optional and can be called during setup."""
        try:
            logger.info("Initializing member facts for all members")
            members = sample_members()  # Returns List[Member]
            successful = 0
            failed = 0

            for member in members:
                member_dict = asdict(member)  # Convert dataclass to dict
                result = json.loads(add_member_facts(member_dict))
                if result.get("success"):
                    successful += 1
                    logger.debug(f"Successfully initialized facts for member {member.id}")
                else:
                    failed += 1
                    logger.warning(f"Failed to initialize facts for member {member.id}: {result.get('error')}")

            logger.info(f"Member facts initialization complete: {successful} successful, {failed} failed")
            return {"successful": successful, "failed": failed, "total": len(members)}
        except Exception as e:
            logger.error(f"Error initializing member facts: {e}", exc_info=True)
            return {"successful": 0, "failed": 0, "total": 0, "error": str(e)}

    def _determine_priority_mission(self, question, user_id):
        """Determine which mission should be prioritized based on the question and context"""
        logger.info(f"Determining priority mission for user_id={user_id}")

        try:
            # Get member information
            members = sample_members()
            member = next((m for m in members if m.id == user_id), None)

            if not member:
                return None

            # Get all missions
            missions = sample_missions()
            member_missions = [m for m in missions if m.vertical == member.vertical]

            if not member_missions:
                return None

            # Get conversation history and interactions
            past_memories = self.get_memories(user_id=user_id)
            conversation_context = (
                "\n".join([f"- {memory}" for memory in past_memories[-5:]])
                if past_memories
                else "No previous conversation"
            )

            # Get member interactions for additional context
            interactions = get_member_interactions(user_id)
            interaction_signals = ""
            if interactions:
                interaction_signals = "\n\nRecent Interaction Signals:\n"
                for interaction in interactions[-3:]:  # Last 3 interactions
                    interaction_signals += f"- [{interaction.signal.upper()}] {interaction.title}\n"
                interaction_signals += "\nNote: NEGATIVE/WARNING signals indicate retention priority; POSITIVE signals may indicate growth opportunity.\n"

            # Use AI to determine priority mission
            priority_prompt = f"""Based on the user's current question, recent conversation history, and interaction signals, determine which mission should be the PRIORITY for this response.

Available Missions:
{chr(10).join([f"- {m.title}: {m.description}" for m in member_missions])}

Mission Priority Guidelines:
1. HIGH-VALUE RETENTION takes priority if:
   - User expresses dissatisfaction, complaints, or concerns about services/fees
   - User mentions competitors or thinking of leaving
   - User shows signs of decreased engagement or frustration
   - User needs immediate attention to prevent churn
   - Interaction signals show NEGATIVE or WARNING patterns

2. INVESTMENT PRODUCT ADOPTION takes priority if:
   - User asks about investment options, savings growth, or financial planning
   - User shows interest in new products or services
   - User is exploring ways to grow wealth
   - No urgent retention issues are present
   - Interaction signals show POSITIVE engagement

Recent Conversation:
{conversation_context}
{interaction_signals}

Current Question: {question}

Instructions:
- Analyze the question, conversation context, AND interaction signals carefully
- Determine which mission is MOST CRITICAL right now
- Return ONLY the exact mission title, nothing else

Priority Mission:"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": priority_prompt}],
                max_tokens=50,
                temperature=0.3,
            )

            priority_mission_title = response.choices[0].message.content.strip()

            # Find the mission object
            priority_mission = next((m for m in member_missions if m.title == priority_mission_title), None)

            if priority_mission:
                logger.info(f"Priority mission determined: {priority_mission.title}")
                return priority_mission
            else:
                logger.warning(f"Could not match priority mission '{priority_mission_title}', using first mission")
                return member_missions[0]

        except Exception as e:
            logger.error(f"Error determining priority mission: {e}", exc_info=True)
            return None

    def _generate_response(self, messages):
        """Generate a response from the AI without tool calling"""
        logger.debug("Generating response from OpenAI API")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.3,  # Moderate temperature for natural conversation
                max_tokens=150,  # Allow brief, complete responses (100 tokens = ~75 words)
            )
            logger.debug("Received response from OpenAI API")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            raise

    def ask_question(self, question, user_id):
        """Ask a question and get a response from the agent

        Returns:
            str: The answer text
        """
        logger.info(f"Processing question for user_id={user_id}")

        # STEP 1: Determine priority mission BEFORE responding
        priority_mission = self._determine_priority_mission(question, user_id)

        if priority_mission:
            logger.info(f"🎯 PRIORITY MISSION: {priority_mission.title}")
        else:
            logger.warning("No priority mission determined")

        # Get past conversations from memory
        past_memories = self.get_memories(user_id=user_id)
        logger.debug(f"Retrieved {len(past_memories)} past memories for user_id={user_id}")

        # Retrieve relevant context from knowledge base using RAG
        rag_context = ""
        try:
            rag_system = get_rag_system()
            if rag_system.is_loan_related_query(question):
                rag_context = rag_system.retrieve_relevant_context(question, top_k=2)
                if rag_context:
                    logger.info("Retrieved relevant context from knowledge base")
                else:
                    logger.debug("No relevant context found in knowledge base")
            else:
                logger.debug("Question not loan-related, skipping RAG retrieval")
        except Exception as e:
            logger.error(f"Error retrieving RAG context: {e}", exc_info=True)
            # Continue without RAG context

        logger.info("Rag context is as follows %s", rag_context)

        # STEP 2: Build mission-focused system message
        base_message = self.system_message

        # Add priority mission context to tune the response
        if priority_mission:
            mission_context = f"""

=== PRIORITY MISSION (CRITICAL) ===
Mission: {priority_mission.title}
Description: {priority_mission.description}
Goal: {priority_mission.end_goal}

IMPORTANT INSTRUCTIONS FOR THIS RESPONSE:
- This is the CRITICAL MISSION that requires immediate attention
- Tailor your response to address this mission's objectives
- If the mission is "High-Value Retention", prioritize:
  * Addressing concerns immediately and empathetically
  * Offering solutions to prevent churn
  * Showing value and building trust
  * Being proactive about resolving issues
- If the mission is "Investment Product Adoption", prioritize:
  * Educating about investment opportunities
  * Building confidence in financial products
  * Addressing concerns about risk
  * Guiding towards next steps

Your response MUST be tuned to advance this priority mission.
=== End Priority Mission Context ===
"""
            base_message += mission_context

        # Add knowledge base context if available
        if rag_context:
            base_message += (
                "\n\n=== Knowledge Base Information ===\n"
                "Use the following information to answer questions accurately. "
                "This is authoritative information about our loan products:\n\n"
                f"{rag_context}\n"
                "=== End of Knowledge Base ===\n"
            )

        # Add conversation history
        if past_memories:
            conversation_history = "\n".join([f"- {memory}" for memory in past_memories])
            enhanced_system_message = (
                f"{base_message}\n\n"
                f"=== Conversation History ===\n{conversation_history}\n"
                f"=== End of History ===\n\n"
                f"Remember: Continue this conversation naturally. The user doesn't need to be reminded that you have their history - "
                f"just demonstrate it through your responses by naturally building on what was discussed before."
            )
            logger.debug("Enhanced system message with past conversation context, RAG, and priority mission")
        else:
            enhanced_system_message = (
                f"{base_message}\n\n"
                f"This is a new conversation with no prior history. Greet the user warmly and help them get started."
            )
            logger.debug("No past memories found, using default system message with RAG context and priority mission")

        messages = [
            {"role": "system", "content": enhanced_system_message},
            {"role": "user", "content": question},
        ]

        # Generate response from AI (now tuned to priority mission)
        answer = self._generate_response(messages)

        # Store the conversation in memory asynchronously (non-blocking)
        # This prevents the 3-4 second delay from blocking the user's response
        conversation_messages = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
        async_add_memory(json.dumps(conversation_messages), user_id)
        logger.info(f"Conversation queued for async storage for user_id={user_id}")

        return clean_text(answer)

    def get_conversation_summary(self, user_id):
        """Get a detailed insight summary for a user including member info and Wyzion's analysis"""
        logger.info(f"Generating conversation summary for user_id={user_id}")

        # Get member information
        members = sample_members()  # Returns List[Member]
        member = next((m for m in members if m.id == user_id), None)

        if member is None:
            logger.warning(f"Member with id={user_id} not found")
            member_name = "Unknown Member"
            member_data = {}
            lifecycle_state = "No Active Journey"
            priority_mission = None
            all_mission_statuses = []
        else:
            member_data = asdict(member)  # Convert to dict for compatibility
            member_name = member.name

            # Use tracked stage if available, otherwise use default
            current_stage = stage_tracker.get_stage(user_id, member.current_stage)
            member_data["current_stage"] = current_stage  # Update member_data with tracked stage

            # Get mission based on member's vertical
            missions = sample_missions()  # Returns List[Mission]
            mission = next((m for m in missions if m.vertical == member.vertical), None)

            if mission:
                lifecycle_state = f"{mission.title} - {current_stage}"
            else:
                lifecycle_state = current_stage if current_stage != "Unknown" else "No Active Journey"

            # Get priority mission and all mission statuses for analysis
            all_mission_statuses = self.get_all_mission_statuses(user_id)

            # Determine priority mission for this summary
            memories = self.get_memories(user_id)
            if memories:
                # Use last message to determine current priority
                last_message = memories[-1] if memories else ""
                priority_mission = self._determine_priority_mission(last_message, user_id)
                logger.info(
                    f"🎯 Priority mission for summary: {priority_mission.title if priority_mission else 'None'}"
                )
            else:
                priority_mission = None

        memories = self.get_memories(user_id)

        # Get member interactions
        interactions = get_member_interactions(user_id)

        if not memories:
            logger.info("No memories found for summary")
            return {
                "member_name": member_name,
                "lifecycle_state": lifecycle_state,
                "analysis": "No conversation history yet. Start engaging to build insights.",
                "interactions": [asdict(i) for i in interactions],
            }

        # Get conversation history text
        conversation_text = "\n".join(memories)

        # Get member details for banking context
        member_context = ""
        if member_data:
            vertical = member_data.get("vertical", "BFSI")
            member_context = f"\n\nMember Details:\n- Name: {member_data.get('name')}\n"
            member_context += f"- Vertical: {vertical}\n"
            member_context += f"- Persona: {member_data.get('persona', 'N/A')}\n"
            member_context += f"- Age: {member_data.get('age')}\n"
            member_context += f"- Current Stage: {member_data.get('current_stage')}\n"
            member_context += f"- Goal: {member_data.get('goal', 'N/A')}\n"
            member_context += f"- Credit Score: {member_data.get('credit_score', 'N/A')}\n"
            member_context += f"- Transaction Volume: ${member_data.get('transaction_volume', 0):,.2f}\n"
            member_context += f"- Current Products: {', '.join(member_data.get('current_products', []))}\n"
            member_context += f"- Risk Level: {member_data.get('risk_level', 'N/A')}\n"

        # Build mission status context
        mission_status_context = ""
        if all_mission_statuses:
            mission_status_context = "\n\nAll Mission Statuses:\n"
            for mission_status in all_mission_statuses:
                mission_status_context += f"- {mission_status['mission_title']}: {mission_status['current_stage']}\n"

        # Build priority mission context
        priority_mission_context = ""
        if priority_mission:
            priority_mission_context = "\n\n🎯 PRIORITY MISSION (CRITICAL):\n"
            priority_mission_context += f"- Mission: {priority_mission.title}\n"
            priority_mission_context += f"- Description: {priority_mission.description}\n"
            priority_mission_context += f"- Goal: {priority_mission.end_goal}\n"
            # Find the current stage for this priority mission
            priority_mission_stage = "Unknown"
            for mission_status in all_mission_statuses:
                if mission_status["mission_title"] == priority_mission.title:
                    priority_mission_stage = mission_status["current_stage"]
                    break
            priority_mission_context += f"- Current Stage: {priority_mission_stage}\n"

        # Create an enhanced analysis using the LLM focused on banking
        vertical = member_data.get("vertical", "BFSI") if member_data else "BFSI"

        # Determine risk metric based on member's mission/goal
        risk_level = member_data.get("risk_level", "low") if member_data else "low"
        if risk_level == "high" or "churn" in lifecycle_state.lower() or "at risk" in lifecycle_state.lower():
            risk_metric = "churn probability"
        else:
            risk_metric = "investment readiness score"

        # Build interaction history context for analysis
        interaction_analysis_context = ""
        if interactions:
            interaction_analysis_context = "\n\nRecent Interaction Signals:\n"
            for interaction in interactions[-5:]:  # Last 5 interactions
                interaction_analysis_context += f"- [{interaction.timestamp}] {interaction.signal.upper()}: {interaction.title} - {interaction.description}\n"
            interaction_analysis_context += "\nNote: These interactions show behavioral patterns and sentiment signals that should inform your analysis.\n"

        analysis_prompt = (
            f"You are Wyzion AI, an advanced analytics system for Banking & Financial Services. "
            f"Analyze the member's data and provide a BRIEF analysis in this EXACT format:\n\n"
            f"Recommendation: [One clear, actionable recommendation for what should be done next. "
            f"Be specific and direct - focus on the immediate action needed]\n\n"
            f"Wyzion explains why: [Brief explanation including the {risk_metric} percentage and key behavioral insight]\n\n"
            f"Member Context:{member_context}\n"
            f"{mission_status_context}"
            f"{priority_mission_context}\n"
            f"Current Journey: {lifecycle_state}\n\n"
            f"Conversation History:\n{conversation_text}\n"
            f"{interaction_analysis_context}\n"
            f"IMPORTANT INSTRUCTIONS:\n"
            f"- Keep response concise (2-3 sentences total)\n"
            f"- Start with 'Recommendation:' on first line\n"
            f"- Follow with 'Wyzion explains why:' on next line\n"
            f"- Include the {risk_metric} percentage in the explanation\n"
            f"- Consider interaction signals (positive/negative/warning) when forming your analysis\n"
            f"- DO NOT explicitly mention mission names (like 'High-Value Retention' or 'Investment Product Adoption')\n"
            f"- DO NOT mention stages (like 'At Risk', 'Consideration', etc.)\n"
            f"- Use the mission and stage information internally to inform your recommendation\n"
            f"- Focus on natural, actionable business language\n"
            f"- Be specific about what action to take (e.g., 'Schedule retention call', 'Waive account fees', 'Recommend SIP investment')\n"
            f"- Prioritize based on the PRIORITY MISSION context provided above"
        )

        try:
            # Get Wyzion's analysis
            analysis_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are Wyzion AI, a sophisticated analytics engine that provides actionable insights for Banking & Financial Services organizations. Always be brief and concise.",
                    },
                    {"role": "user", "content": analysis_prompt},
                ],
                temperature=0.4,
                max_tokens=150,  # Limit to ~100 words for quick insights
            )
            analysis = analysis_response.choices[0].message.content

            logger.info("Conversation insight summary generated successfully")
            return {
                "member_name": member_name,
                "lifecycle_state": lifecycle_state,
                "analysis": analysis,
                "interactions": [asdict(i) for i in interactions],
            }
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}", exc_info=True)
            raise

    def get_memories(self, user_id):
        """
        Get all memories for a user, merging both cached (pending) and persisted (Mem0) memories.

        This ensures that:
        - Recent conversations (still syncing to Mem0) are immediately available
        - Historical conversations (already in Mem0) are included
        - Summaries and intents have complete, up-to-date conversation history
        """
        # Get memories from Mem0 (persisted, might be slightly behind)
        result = json.loads(get_all_memories(user_id))
        mem0_memories = result.get("memories", [])
        logger.debug(f"Retrieved {len(mem0_memories)} memories from Mem0 for user_id={user_id}")

        # Get memories from local cache (most recent, might not be in Mem0 yet)
        cached_memories = memory_cache.get(user_id)
        logger.debug(f"Retrieved {len(cached_memories)} cached memories for user_id={user_id}")

        # Merge: Mem0 memories first (older), then cached memories (newer)
        # This ensures chronological order and latest conversations are included
        all_memories = mem0_memories + cached_memories

        logger.info(
            f"Total memories for user_id={user_id}: {len(all_memories)} "
            f"(Mem0: {len(mem0_memories)}, Cache: {len(cached_memories)})"
        )

        return all_memories

    def search_memories(self, query, user_id):
        """Search memories for a user"""
        result = json.loads(search_memories(query, user_id))
        return result.get("memories", [])

    def transcribe_audio(self, audio_file):
        with open(audio_file, "rb") as f:
            transcript = self.client.audio.transcriptions.create(model="whisper-1", file=f)
        return clean_text(transcript.text)

    def speak_answer(self, text, out_file="answer.wav"):
        with self.client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts", voice="verse", input=text
        ) as response:
            response.stream_to_file(out_file)
        return out_file

    def _get_vertical_stage_guidance(self):
        """
        Get stage detection guidance for banking missions

        Returns detailed indicators for each stage transition to improve accuracy
        """
        return """
Stage Detection Indicators for BFSI Banking:

INVESTMENT PRODUCT ADOPTION MISSION:
1. Loyal Member → Opportunity Detected:
   - Member expresses financial goals or savings patterns
   - Asks about investment options, mutual funds, or better returns
   - Shows interest in growing wealth beyond basic savings
   - Keywords: "savings", "grow", "mutual funds", "investment", "better returns"

2. Opportunity Detected → Consideration:
   - Asks specific questions about SIP mechanism and how it works
   - Expresses risk concerns or wants to understand market volatility
   - Discusses specific investment amounts (e.g., "5000 per month")
   - Seeks guidance on which funds to choose
   - Keywords: "SIP", "how does it work", "risk", "market crash", "which fund", "amount"

3. Consideration → Multi-Product Member:
   - Explicitly states readiness to start ("I'm ready", "let's start")
   - Requests help with account opening or KYC process
   - Makes specific investment decisions (e.g., "balanced fund, 5000 per month")
   - Confirms first investment or SIP setup
   - Keywords: "ready to start", "next step", "set this up", "first installment", "went through"

HIGH-VALUE RETENTION MISSION:
1. Active Member → At Risk:
   - Expresses dissatisfaction with fees, services, or account features
   - Mentions competitor banks or compares services
   - Discusses reducing account usage or closing account
   - Shows decreased engagement or transaction activity
   - Keywords: "too expensive", "other banks", "thinking of switching", "not using", "close account"

2. At Risk → Re-engagement:
   - Shows interest in retention offers or benefits
   - Asks about fee waivers or account upgrades
   - Responds positively to personalized outreach
   - Engages with relationship manager or support
   - Keywords: "what can you offer", "waive fees", "better deal", "interested in", "tell me more"

3. Re-engagement → Retained Member:
   - Accepts retention offer or upgraded service
   - Confirms continued use of account and services
   - Expresses renewed satisfaction with the bank
   - Plans to maintain or increase banking relationship
   - Keywords: "sounds good", "I'll stay", "satisfied", "makes sense", "continue banking"
"""

    def get_all_mission_statuses(self, user_id):
        """Analyze conversation and determine the status for all missions"""
        logger.info(f"Getting all mission statuses for user_id={user_id}")

        try:
            # Get member information
            members = sample_members()
            member = next((m for m in members if m.id == user_id), None)

            if member is None:
                logger.warning(f"Member with id={user_id} not found")
                return []

            # Get all missions for this member's vertical
            missions = sample_missions()
            member_missions = [m for m in missions if m.vertical == member.vertical]

            # Get conversation history and interactions
            past_memories = self.get_memories(user_id=user_id)
            interactions = get_member_interactions(user_id)

            mission_statuses = []

            for mission in member_missions:
                # Determine status based on conversation
                if past_memories:
                    # Get stages for this mission
                    stage_names = mission.stages

                    conversation_history = "\n".join([f"- {memory}" for memory in past_memories[-10:]])

                    # Get stage detection guidance
                    vertical_guidance = self._get_vertical_stage_guidance()

                    # Build interaction history context
                    interaction_context = ""
                    if interactions:
                        interaction_context = "\n\nRecent Interactions:\n"
                        for interaction in interactions[-5:]:  # Last 5 interactions
                            interaction_context += (
                                f"- [{interaction.timestamp}] {interaction.title}: {interaction.description}\n"
                            )

                    # Create a prompt to analyze this specific mission
                    status_prompt = f"""Based on the conversation history and interaction signals, determine the current status for this mission.

Member Profile:
- Name: {member.name}
- Vertical: {member.vertical}
- Persona: {member.persona}
- Goal: {member.goal}

Mission: {mission.title}
Available Stages: {', '.join(stage_names)}

{vertical_guidance}

Recent Conversation:
{conversation_history}
{interaction_context}

Instructions:
- Analyze BOTH the conversation and interaction signals to understand the member's status for this specific mission
- Interactions provide behavioral signals (positive/negative/warning/neutral) that indicate member sentiment
- Return ONLY the exact stage name from the available stages
- If there's no clear indication in the conversation, use the first stage: {stage_names[0]}

Current Stage:"""

                    try:
                        response = self.client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": status_prompt}],
                            max_tokens=50,
                            temperature=0.3,
                        )
                        detected_stage = response.choices[0].message.content.strip()

                        # Validate stage
                        if detected_stage in stage_names:
                            current_stage = detected_stage
                        else:
                            current_stage = stage_names[0]
                            logger.warning(
                                f"AI returned invalid stage '{detected_stage}', using default: {current_stage}"
                            )

                    except Exception as e:
                        logger.error(f"Error detecting stage for mission {mission.title}: {e}")
                        current_stage = stage_names[0]
                else:
                    # No conversation yet, use first stage
                    current_stage = mission.stages[0]

                mission_statuses.append(
                    {
                        "mission_id": mission.mission_id,
                        "mission_title": mission.title,
                        "current_stage": current_stage,
                        "stages": mission.stages,
                    }
                )

            logger.info(f"Retrieved {len(mission_statuses)} mission statuses for user_id={user_id}")
            return mission_statuses

        except Exception as e:
            logger.error(f"Error getting mission statuses: {e}", exc_info=True)
            return []


# --------------------------
# Flask App
# --------------------------
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "../templates"))
ai_assistant = BankingAssistant()

# Auto-initialize member facts on startup
logger.info("Auto-initializing member facts in mem0...")
try:
    init_result = ai_assistant.initialize_member_facts_for_all()
    if init_result.get("successful", 0) > 0:
        logger.info(f"✓ Member facts auto-initialized: {init_result['successful']}/{init_result['total']} members")
    else:
        logger.warning(f"⚠ Member facts auto-initialization had issues: {init_result}")
except Exception as e:
    logger.error(f"✗ Failed to auto-initialize member facts: {e}", exc_info=True)


@app.route("/")
def index():
    logger.info("Index page accessed")
    return render_template("chat.html")


@app.route("/get_members", methods=["GET"])
def get_members():
    """Get list of all members"""
    try:
        logger.info("Fetching members list")
        members = sample_members()  # Returns List[Member]

        # Convert dataclasses to dicts, excluding None values
        members_list = []
        for member in members:
            member_dict = asdict(member)
            # Update with tracked stage if available
            if stage_tracker.has_stage(member.id):
                member_dict["current_stage"] = stage_tracker.get_stage(member.id)
                logger.debug(f"Using tracked stage for {member.id}: {member_dict['current_stage']}")
            # Remove None values for cleaner JSON
            member_dict = {k: v for k, v in member_dict.items() if v is not None}
            members_list.append(member_dict)

        logger.info(f"Retrieved {len(members_list)} members")
        return jsonify({"members": members_list})
    except Exception as e:
        logger.error(f"Error in get_members endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/initialize_member_facts", methods=["POST"])
def initialize_member_facts():
    """Initialize member facts in memory for all members or a specific member"""
    try:
        data = request.json
        member_id = data.get("member_id") if data else None

        logger.info("Initializing member facts in memory")
        members = sample_members()  # Returns List[Member]

        # Filter to specific member if requested
        if member_id:
            members = [m for m in members if m.id == member_id]
            if not members:
                logger.warning(f"Member with id={member_id} not found")
                return jsonify({"error": f"Member {member_id} not found"}), 404

        # Store facts for each member
        results = []
        for member in members:
            member_dict = asdict(member)  # Convert dataclass to dict
            result = json.loads(add_member_facts(member_dict))
            results.append(
                {
                    "member_id": member.id,
                    "name": member.name,
                    "success": result.get("success"),
                    "message": result.get("message"),
                    "error": result.get("error"),
                }
            )

        successful = sum(1 for r in results if r["success"])
        logger.info(f"Member facts initialized: {successful}/{len(results)} successful")

        return jsonify(
            {
                "success": successful == len(results),
                "initialized_count": successful,
                "total_count": len(results),
                "results": results,
            }
        )
    except Exception as e:
        logger.error(f"Error in initialize_member_facts endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/ask_text", methods=["POST"])
def ask_text():
    try:
        data = request.json
        question = data.get("question", "")
        user_id = data.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Received text question from user_id={user_id}: {question[:100]}...")

        if not question:
            logger.warning("Empty question received")
            return jsonify({"error": "Question missing"}), 400

        answer = ai_assistant.ask_question(question, user_id=user_id)
        logger.info(f"Successfully generated answer for user_id={user_id}")

        # Return just the answer - intent will be refreshed manually via button
        return jsonify({"answer": answer})
    except Exception as e:
        logger.error(f"Error in ask_text endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    try:
        user_id = request.form.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Received audio upload from user_id={user_id}")

        if "audio" not in request.files:
            logger.warning("Audio file missing in request")
            return jsonify({"error": "Audio file missing"}), 400

        file = request.files["audio"]
        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
        file.save(tmpfile)
        logger.debug(f"Audio file saved to {tmpfile}")

        transcript = ai_assistant.transcribe_audio(tmpfile)
        logger.info(f"Audio transcribed: {transcript[:100]}...")

        answer = ai_assistant.ask_question(transcript, user_id=user_id)
        logger.info("Generated answer from transcript")

        speech_file = ai_assistant.speak_answer(answer)
        logger.info(f"Generated speech file: {speech_file}")

        return jsonify({"transcript": transcript, "answer": answer, "speech_file": speech_file})
    except Exception as e:
        logger.error(f"Error in upload_audio endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/download/<filename>")
def download(filename):
    return send_file(filename, as_attachment=True)


@app.route("/conversation_summary", methods=["GET"])
def conversation_summary():
    """Get a detailed insight summary with member info and Wyzion's analysis"""
    try:
        user_id = request.args.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Generating conversation summary for user_id={user_id}")
        summary_data = ai_assistant.get_conversation_summary(user_id=user_id)
        logger.info("Conversation summary generated successfully")
        return jsonify(summary_data)
    except Exception as e:
        logger.error(f"Error in conversation_summary endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/all_mission_statuses", methods=["GET"])
def all_mission_statuses():
    """Get all mission statuses for a user"""
    try:
        user_id = request.args.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Getting all mission statuses for user_id={user_id}")
        statuses = ai_assistant.get_all_mission_statuses(user_id=user_id)
        logger.info(f"Retrieved {len(statuses)} mission statuses")
        return jsonify({"missions": statuses})
    except Exception as e:
        logger.error(f"Error in all_mission_statuses endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Get port and debug mode from environment variables
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_ENV", "development") == "development"

    logger.info("=" * 60)
    logger.info("Starting Wyzion Mem0 AI Demo Application")
    logger.info(f"Flask Debug Mode: {debug_mode}")
    logger.info(f"Server Port: {port}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info("=" * 60)

    app.run(debug=debug_mode, host="0.0.0.0", port=port)
