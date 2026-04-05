from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

# Construct the path to the .env file in the project root
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

app = Flask(__name__)
CORS(app)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY or API_KEY == "YOUR_GEMINI_API_KEY":
    raise ValueError("GEMINI_API_KEY not found or not set in .env file. Please get a key from https://aistudio.google.com/ and set it in the .env file in the project root.")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')
    context_data = data.get('context')

    if not question or not context_data:
        return jsonify({'error': 'Question and context data are required.'}), 400

    try:
        # Create a string representation of the context for the prompt
        context_str = json.dumps(context_data, indent=2)

        # Limit context size to avoid overly large prompts
        if len(context_str) > 30000:
            context_str = context_str[:30000] + "\n... (context truncated)"


        prompt = f"""
        You are a helpful assistant for a building information modeling (BIM) clash report.
        Your task is to answer questions based on the provided JSON data context.
        The user is viewing a web-based report and has a question.
        
        Here is the data from the report:
        {context_str}

        Here is the user's question:
        "{question}"

        Based on the data, provide a concise and helpful answer. If the data does not contain the answer, say so.
        """

        response = model.generate_content(prompt)
        
        return jsonify({'answer': response.text})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
