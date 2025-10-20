import json
import os
import tempfile

from flask import Flask, jsonify, render_template, request, send_file
from openai import OpenAI

from wyzion_mem0_ai_demo.data.missions import sample_members, sample_missions
from wyzion_mem0_ai_demo.helper.json_formatting import clean_text, extract_json
from wyzion_mem0_ai_demo.tools.memory_tools import (
    add_memory,
    get_all_memories,
    initialize_memory_client,
    search_memories,
)
from wyzion_mem0_ai_demo.utils.logger import configure_third_party_loggers, get_logger

# Initialize logger
logger = get_logger(__name__)
configure_third_party_loggers()


# --------------------------
# Helper functions
# --------------------------
def get_missions_text():
    missions_df = sample_missions()
    mission_pairs = []
    for _, row in missions_df.iterrows():
        for stage in row["stages"]:
            mission_pairs.append(f"({row['title']}, {stage})")
    return ", ".join(mission_pairs)


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

        self.system_message = (
            "You are a helpful financial AI Assistant for a credit union. "
            "When past conversation history is provided, seamlessly continue the conversation as if it's an ongoing dialogue. "
            "Reference previous discussions naturally, acknowledge the user's past questions and concerns, "
            "and build upon what was previously discussed without explicitly saying 'based on our previous conversation' unless contextually appropriate. "
            "Make the user feel understood and valued by demonstrating awareness of their financial journey with the credit union. "
            "Provide personalized, helpful, professional, and accurate financial guidance that feels like a warm continuation of an existing relationship."
        )
        logger.info("CreditUnionAssistant initialized successfully")

    def _generate_response(self, messages):
        """Generate a response from the AI without tool calling"""
        logger.debug("Generating response from OpenAI API")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o", messages=messages, temperature=0.3  # Moderate temperature for natural conversation
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

        # Build enhanced system message with conversation history
        if past_memories:
            conversation_history = "\n".join([f"- {memory}" for memory in past_memories])
            enhanced_system_message = (
                f"{self.system_message}\n\n"
                f"=== Conversation History ===\n{conversation_history}\n"
                f"=== End of History ===\n\n"
                f"Remember: Continue this conversation naturally. The user doesn't need to be reminded that you have their history - "
                f"just demonstrate it through your responses by naturally building on what was discussed before."
            )
            logger.debug("Enhanced system message with past conversation context")
        else:
            enhanced_system_message = (
                f"{self.system_message}\n\n"
                f"This is a new conversation with no prior history. Greet the user warmly and help them get started."
            )
            logger.debug("No past memories found, using default system message with new user context")

        messages = [
            {"role": "system", "content": enhanced_system_message},
            {"role": "user", "content": question},
        ]

        # Generate response from AI
        answer = self._generate_response(messages)

        # Store the conversation in memory after getting the answer
        conversation_messages = [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
        add_memory(json.dumps(conversation_messages), user_id)
        logger.info(f"Conversation stored in memory for user_id={user_id}")

        return clean_text(answer)

    def get_conversation_summary(self, user_id):
        """Get a summary of all conversations for a user"""
        logger.info(f"Generating conversation summary for user_id={user_id}")
        memories = self.get_memories(user_id)
        if not memories:
            logger.info("No memories found for summary")
            return "No conversation history yet."

        # Create a summary using the LLM
        summary_prompt = (
            "Summarize the following conversation history in bullet points, "
            "highlighting key topics discussed and important details:\n\n" + "\n".join(memories)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that creates concise summaries."},
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0.3,  # Low temperature for consistent, factual summaries
            )
            logger.info("Conversation summary generated successfully")
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating conversation summary: {e}", exc_info=True)
            raise

    def get_memories(self, user_id):
        """Get all memories for a user"""
        result = json.loads(get_all_memories(user_id))
        print(result)
        return result.get("memories", [])

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

    def classify_mission(self, user_id):
        """Classify the user's current mission and stage based on conversation history"""
        logger.info(f"Classifying mission for user_id={user_id}")
        previous_memories = self.get_memories(user_id=user_id)
        conversation_history = "\n".join(previous_memories) if previous_memories else "No prior conversation."
        missions_text = get_missions_text()

        system_message = (
            "You are an AI Assistant who identifies the mission and the corresponding stage of a user "
            "based on their conversation history strictly in the missions and stages mentioned below only.\n\n"
            f"Missions and stages:\n{missions_text}\n\n"
            f"Conversation history:\n{conversation_history}\n\n"
            "Return your answer strictly in JSON with keys: mission_id, stage, explanation."
        )

        try:
            # Using chat completions API with structured output for consistency
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing conversation history and classifying user missions. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": system_message},
                ],
                temperature=0.1,  # Very low temperature for consistent classification
                response_format={"type": "json_object"},  # Ensure JSON response
            )

            raw_answer = response.choices[0].message.content
            logger.debug(f"Raw classification response: {raw_answer}")

            try:
                answer = extract_json(raw_answer)
                logger.info(
                    f"Successfully classified mission: {answer.get('mission_id', 'Unknown')}, Stage: {answer.get('stage', 'Unknown')}"
                )
            except Exception as e:
                logger.error(f"Failed to extract JSON from classification response: {e}")
                answer = {
                    "mission_id": "Unknown",
                    "stage": "Unknown",
                    "explanation": raw_answer,
                }
        except Exception as e:
            logger.error(f"Error in mission classification: {e}", exc_info=True)
            answer = {
                "mission_id": "Unknown",
                "stage": "Unknown",
                "explanation": f"Error: {str(e)}",
            }

        return answer


# --------------------------
# Flask App
# --------------------------
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "../templates"))
ai_assistant = CreditUnionAssistant()


@app.route("/")
def index():
    logger.info("Index page accessed")
    return render_template("chat.html")


@app.route("/get_members", methods=["GET"])
def get_members():
    """Get list of all members"""
    try:
        logger.info("Fetching members list")
        members_df = sample_members()
        members_list = members_df.to_dict(orient="records")
        logger.info(f"Retrieved {len(members_list)} members")
        return jsonify({"members": members_list})
    except Exception as e:
        logger.error(f"Error in get_members endpoint: {e}", exc_info=True)
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
    """Get a summary of the conversation history"""
    try:
        user_id = request.args.get("user_id", "")

        if not user_id:
            logger.warning("user_id missing in request")
            return jsonify({"error": "user_id missing"}), 400

        logger.info(f"Generating conversation summary for user_id={user_id}")
        summary = ai_assistant.get_conversation_summary(user_id=user_id)
        logger.info("Conversation summary generated successfully")
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Error in conversation_summary endpoint: {e}", exc_info=True)
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
