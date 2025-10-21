import json
import os
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from threading import Lock

from flask import Flask, jsonify, render_template, request, send_file
from openai import OpenAI

from wyzion_mem0_ai_demo.data.models import (
    get_member_interactions,
    get_stages_by_vertical,
    sample_members,
    sample_missions,
)
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
class CreditUnionAssistant:
    def __init__(self):
        logger.info("Initializing CreditUnionAssistant")
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
            "You are a helpful AI Assistant that adapts to different industries (BFSI, Healthcare, E-commerce). "
            "When past conversation history is provided, seamlessly continue the conversation as if it's an ongoing dialogue. "
            "Reference previous discussions naturally, acknowledge the user's past questions and concerns, "
            "and build upon what was previously discussed without explicitly saying 'based on our previous conversation' unless contextually appropriate. "
            "Make the user feel understood and valued by demonstrating awareness of their journey. "
            "Provide personalized, helpful, professional, and accurate guidance that feels like a warm continuation of an existing relationship. "
            "When member/user-specific facts are available in the conversation history (such as name, age, vertical, persona, current stage, goals), "
            "use them naturally to provide personalized responses appropriate to their industry context. "
            "\n\nIMPORTANT: Keep responses brief and concise (2-3 sentences max). Provide quick, actionable insights."
        )
        logger.info("CreditUnionAssistant initialized successfully")

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

        # Build enhanced system message with conversation history and knowledge base
        base_message = self.system_message

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
            logger.debug("Enhanced system message with past conversation context and RAG")
        else:
            enhanced_system_message = (
                f"{base_message}\n\n"
                f"This is a new conversation with no prior history. Greet the user warmly and help them get started."
            )
            logger.debug("No past memories found, using default system message with RAG context")

        messages = [
            {"role": "system", "content": enhanced_system_message},
            {"role": "user", "content": question},
        ]

        # Generate response from AI
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

        memories = self.get_memories(user_id)

        # Get member interactions
        interactions = get_member_interactions(user_id)

        if not memories:
            logger.info("No memories found for summary")
            return {
                "member_name": member_name,
                "lifecycle_state": lifecycle_state,
                "analysis": "No conversation history yet. Start engaging to build insights.",
                "interactions": interactions,
            }

        # Get conversation history text
        conversation_text = "\n".join(memories)

        # Get member details for context based on vertical
        member_context = ""
        if member_data:
            vertical = member_data.get("vertical", "")
            member_context = f"\n\nMember Details:\n- Name: {member_data.get('name')}\n"
            member_context += f"- Vertical: {vertical}\n"
            member_context += f"- Persona: {member_data.get('persona', 'N/A')}\n"
            member_context += f"- Age: {member_data.get('age')}\n"
            member_context += f"- Current Stage: {member_data.get('current_stage')}\n"
            member_context += f"- Goal: {member_data.get('goal', 'N/A')}\n"

            # Add vertical-specific details
            if vertical == "BFSI":
                member_context += f"- Credit Score: {member_data.get('credit_score', 'N/A')}\n"
                member_context += f"- Transaction Volume: ${member_data.get('transaction_volume', 0):,.2f}\n"
                member_context += f"- Current Products: {', '.join(member_data.get('current_products', []))}\n"
            elif vertical == "Healthcare":
                member_context += f"- Visit Frequency: {member_data.get('visit_frequency', 'N/A')}\n"
                member_context += f"- Current Products: {', '.join(member_data.get('current_products', []))}\n"
            elif vertical == "E-commerce":
                member_context += f"- Session Count: {member_data.get('session_count', 'N/A')}\n"
                member_context += f"- Browsing Behavior: {member_data.get('browsing_behavior', 'N/A')}\n"

        # Create an enhanced analysis using the LLM
        vertical = member_data.get("vertical", "BFSI") if member_data else "BFSI"

        # Determine risk metric based on vertical
        if vertical == "BFSI":
            risk_metric = "churn probability"
        elif vertical == "Healthcare":
            risk_metric = "patient attrition risk"
        elif vertical == "E-commerce":
            risk_metric = "conversion probability"
        else:
            risk_metric = "engagement risk"

        analysis_prompt = (
            f"You are Wyzion AI, an advanced analytics system for {vertical}. "
            f"Analyze the user's data and provide a BRIEF analysis (100 words max) with:\n"
            f"1. {risk_metric} (percentage)\n"
            f"2. Key behavioral pattern\n"
            f"3. Recommended next action\n\n"
            f"Member Context:{member_context}\n\n"
            f"Current Journey: {lifecycle_state}\n\n"
            f"Conversation History:\n{conversation_text}\n\n"
            f"IMPORTANT: Keep response to 2-3 sentences max. Be concise and actionable. "
            f"Format: 'Wyzion has assigned a [X]% {risk_metric}. [Key insight]. [Next action].'"
        )

        try:
            # Get Wyzion's analysis
            analysis_response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are Wyzion AI, a sophisticated analytics engine that provides actionable insights for {vertical} organizations. Always be brief and concise.",
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
                "interactions": interactions,
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

    def _get_vertical_stage_guidance(self, vertical):
        """
        Get vertical-specific stage detection guidance based on TEST_SCENARIOS.md

        Returns detailed indicators for each stage transition to improve accuracy
        """
        if vertical == "BFSI":
            return """
Stage Detection Indicators for BFSI:

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
"""
        elif vertical == "Healthcare":
            return """
Stage Detection Indicators for Healthcare:

1. Stable Patient → Proactive Opportunity:
   - Expresses concerns about health metrics (blood pressure, weight)
   - Asks about prevention or avoiding future health problems
   - Shows proactive mindset about health management
   - Interested in lifestyle changes or wellness
   - Keywords: "should I be worried", "prevent", "proactive", "avoid", "future health"

2. Proactive Opportunity → Engagement:
   - Asks specific questions about wellness program details
   - Inquires about personalization and customization of programs
   - Discusses time commitment and program requirements
   - Wants to know expected results and benefits
   - Keywords: "wellness program", "what does it include", "customized", "time commitment", "results"

3. Engagement → Deepened Relationship:
   - Decides to enroll in wellness program
   - Reports starting wellness activities (diet plan, exercise)
   - Shares progress updates and positive outcomes
   - Expresses commitment to long-term wellness
   - Keywords: "enroll", "I'd like to start", "I've started", "following the plan", "continue long-term"
"""
        elif vertical == "E-commerce":
            return """
Stage Detection Indicators for E-commerce:

1. Prospect → Qualified Lead:
   - Looks for specific product types with clear intent
   - Mentions budget range (especially high-value: 40-50k+)
   - Asks for recommendations with specific requirements
   - Compares products or brands
   - Keywords: "looking for", "budget around", "recommend", "tell me more", "comparing"

2. Qualified Lead → Consultation Booked:
   - Seeks expert advice or personal guidance
   - Expresses concerns about size, fit, or customization
   - Indicates this is a significant purchase decision
   - Requests to speak with stylist or expert
   - Keywords: "help me choose", "not sure", "can someone help", "speak to stylist", "personalized"

3. Consultation Booked → First Purchase:
   - Expresses post-consultation confidence
   - Makes specific order decisions with details
   - Asks about returns/policies before finalizing
   - Completes checkout process
   - Confirms order placement
   - Keywords: "ready to buy", "I'd like to order", "check out", "order went through", "when will it arrive"
"""
        else:
            # Generic guidance for unknown verticals
            return """
Stage Detection Indicators:
- Early stages: Questions, exploration, showing interest
- Middle stages: Specific inquiries, consideration of options, seeking details
- Later stages: Decision-making, commitment, taking action
"""

    def classify_mission(self, user_id):
        """Analyze conversation and determine the user's current mission stage"""
        logger.info(f"Getting mission info for user_id={user_id}")

        try:
            # Get member information
            members = sample_members()  # Returns List[Member]
            member = next((m for m in members if m.id == user_id), None)

            if member is None:
                logger.warning(f"Member with id={user_id} not found")
                return {"mission_id": "Unknown", "stage": "Unknown", "explanation": "Member not found"}

            # Get mission based on member's vertical
            missions = sample_missions()  # Returns List[Mission]
            mission = next((m for m in missions if m.vertical == member.vertical), None)

            if mission is None:
                logger.warning(f"No mission found for vertical={member.vertical}")
                return {
                    "mission_id": "Unknown",
                    "stage": member.current_stage,
                    "explanation": f"No mission found for vertical: {member.vertical}",
                }

            # Get conversation history to analyze stage
            past_memories = self.get_memories(user_id=user_id)

            # Determine current stage based on conversation
            if past_memories:
                # Get available stages for this vertical
                stages = get_stages_by_vertical(member.vertical)
                stage_names = [s.stage for s in stages]

                # Use AI to classify the current stage based on conversation
                conversation_history = "\n".join([f"- {memory}" for memory in past_memories[-10:]])  # Last 10 messages

                # Create vertical-specific stage detection guidance based on TEST_SCENARIOS.md
                vertical_guidance = self._get_vertical_stage_guidance(member.vertical)

                stage_prompt = f"""Based on the conversation history below, determine which journey stage the member is currently in.

Member Profile:
- Name: {member.name}
- Vertical: {member.vertical}
- Persona: {member.persona}
- Goal: {member.goal}

Available Journey Stages:
{', '.join(stage_names)}

{vertical_guidance}

Recent Conversation:
{conversation_history}

Instructions:
- Analyze the conversation to understand member behavior and engagement
- Use the stage indicators above to identify the current stage
- Look for specific keywords, phrases, and behavioral patterns mentioned in the indicators
- Select the most appropriate stage from the available stages based on the conversation content
- If the conversation shows clear signs of multiple stages, choose the MOST ADVANCED stage they've reached
- Return ONLY the exact stage name, nothing else

Current Stage:"""

                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": stage_prompt}],
                        max_tokens=50,
                        temperature=0.3,
                    )
                    detected_stage = response.choices[0].message.content.strip()

                    # Validate that the detected stage is in the available stages
                    if detected_stage in stage_names:
                        current_stage = detected_stage
                        logger.info(f"AI detected stage: {current_stage} for user_id={user_id}")
                        # Update the stage tracker
                        stage_tracker.update_stage(user_id, current_stage)
                    else:
                        # Use tracked stage if available, otherwise default
                        current_stage = stage_tracker.get_stage(user_id, member.current_stage)
                        logger.warning(f"AI returned invalid stage '{detected_stage}', using: {current_stage}")
                except Exception as e:
                    logger.error(f"Error detecting stage with AI: {e}")
                    current_stage = stage_tracker.get_stage(user_id, member.current_stage)
            else:
                # No conversation yet, use default stage or tracked stage
                current_stage = stage_tracker.get_stage(user_id, member.current_stage)
                logger.info(f"No conversation history, using stage: {current_stage}")

            logger.info(f"Retrieved mission: {mission.title} ({mission.mission_id}), Stage: {current_stage}")

            return {
                "mission_id": mission.title,  # Return mission title instead of ID
                "stage": current_stage,
                "explanation": f"Member is currently at '{current_stage}' stage in their {mission.title} journey. Goal: {member.goal}",
            }

        except Exception as e:
            logger.error(f"Error getting mission info: {e}", exc_info=True)
            return {"mission_id": "Unknown", "stage": "Unknown", "explanation": f"Error: {str(e)}"}


# --------------------------
# Flask App
# --------------------------
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "../templates"))
ai_assistant = CreditUnionAssistant()

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


@app.post("/classify_mission")
def classify_mission():
    try:
        data = request.json
        user_id = data.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Classifying mission for user_id={user_id}")
        response = ai_assistant.classify_mission(user_id=user_id)
        logger.info(f"Mission classified: {response['mission_id']}, Stage: {response['stage']}")
        return jsonify(
            {
                "mission_id": response["mission_id"],
                "stage": response["stage"],
                "explanation": response["explanation"],
            }
        )
    except Exception as e:
        logger.error(f"Error in classify_mission endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


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


@app.route("/get_stages", methods=["GET"])
def get_stages():
    """Get journey stages for a specific vertical"""
    try:
        vertical = request.args.get("vertical", "")

        if not vertical:
            logger.warning("vertical missing in request")
            return jsonify({"error": "vertical missing"}), 400

        logger.info(f"Fetching stages for vertical={vertical}")
        stages = get_stages_by_vertical(vertical)  # Returns List[JourneyStage]

        # Convert dataclasses to dicts
        stages_list = [asdict(stage) for stage in stages]

        logger.info(f"Retrieved {len(stages_list)} stages for vertical={vertical}")
        return jsonify({"stages": stages_list})
    except Exception as e:
        logger.error(f"Error in get_stages endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


@app.route("/user_intent", methods=["GET"])
def user_intent():
    """Get the user's current mission and stage"""
    try:
        user_id = request.args.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Getting user intent for user_id={user_id}")
        mission_data = ai_assistant.classify_mission(user_id=user_id)
        logger.info(f"User intent retrieved: {mission_data['mission_id']}")
        return jsonify(mission_data)
    except Exception as e:
        logger.error(f"Error in user_intent endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting Wyzion Mem0 AI Demo Application")
    logger.info("Flask Debug Mode: True")
    logger.info("Server Port: 5000")
    logger.info("=" * 60)
    app.run(debug=True, port=5000)
