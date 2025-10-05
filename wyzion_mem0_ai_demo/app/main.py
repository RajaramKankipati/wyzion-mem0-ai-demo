import os
import tempfile

from flask import Flask, jsonify, render_template, request, send_file
from mem0 import MemoryClient
from openai import OpenAI

from wyzion_mem0_ai_demo.data.missions import sample_missions
from wyzion_mem0_ai_demo.helper.json_formatting import clean_text, extract_json


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
# AI Assistant Class
# --------------------------
class CreditUnionAssistant:
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.memory = MemoryClient(api_key=os.environ.get("MEM0_API_KEY"))
        self.messages = [{"role": "system", "content": "You are a financial AI Assistant."}]  # E501

    def ask_question(self, question, user_id):
        previous_memories = self.search_memories(question, user_id=user_id)
        system_message = "You are a financial AI Assistant."
        prompt = f"{system_message}\n\nUser input: {question}"
        if previous_memories:
            prompt += f"\nPrevious memories: {', '.join(previous_memories)}"

        response = self.client.responses.create(model="gpt-4o", input=prompt)
        answer = response.output[0].content[0].text

        user_messages = [
            {"role": "user", "content": question},
            {"role": "system", "content": answer},
        ]
        self.memory.add(user_messages, user_id=user_id, output_format="v1.1")
        return clean_text(answer)

    def get_memories(self, user_id):
        memories = self.memory.get_all(user_id=user_id)
        return [m["memory"] for m in memories]

    def search_memories(self, query, user_id):
        memories = self.memory.search(query, user_id=user_id)
        return [m["memory"] for m in memories]

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

        response = self.client.responses.create(model="gpt-4o", input=system_message)

        raw_answer = response.output[0].content[0].text
        try:
            answer = extract_json(raw_answer)
        except Exception:
            answer = {
                "mission_id": "Unknown",
                "stage": "Unknown",
                "explanation": raw_answer,
            }
        return answer


# --------------------------
# Flask App
# --------------------------
app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), "../templates"))
ai_assistant = CreditUnionAssistant()
USER_ID = "member_1234"


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/ask_text", methods=["POST"])
def ask_text():
    data = request.json
    question = data.get("question", "")
    if not question:
        return jsonify({"error": "Question missing"}), 400
    answer = ai_assistant.ask_question(question, user_id=USER_ID)
    return jsonify({"answer": answer})


@app.route("/upload_audio", methods=["POST"])
def upload_audio():
    if "audio" not in request.files:
        return jsonify({"error": "Audio file missing"}), 400
    file = request.files["audio"]
    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
    file.save(tmpfile)

    transcript = ai_assistant.transcribe_audio(tmpfile)
    answer = ai_assistant.ask_question(transcript, user_id=USER_ID)
    speech_file = ai_assistant.speak_answer(answer)

    return jsonify({"transcript": transcript, "answer": answer, "speech_file": speech_file})


@app.route("/download/<filename>")
def download(filename):
    return send_file(filename, as_attachment=True)


@app.post("/classify_mission")
def classify_mission():
    response = ai_assistant.classify_mission(user_id=USER_ID)
    return jsonify(
        {
            "mission_id": response["mission_id"],
            "stage": response["stage"],
            "explanation": response["explanation"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
