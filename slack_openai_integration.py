from flask import Flask, request, jsonify
import json
import openai
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = Flask(__name__)

# Slack and OpenAI tokens
slack_token = 'SLACK-TOKEN'
openai_api_key = 'OPENAI-TOKEN'

# Slack Client
slack_client = WebClient(token=slack_token)

# OpenAI Client
openai.api_key = openai_api_key

# Specific OpenAI Assistant ID
assistant_id = 'ASSISTANT-ID'

# A dictionary to keep track of conversation states
conversation_states = {}

@app.route('/slack/events', methods=['POST'])
def slack_event():
    data = request.json
    event = data['event']

    if data.get('type') == 'url_verification':
        return jsonify({'challenge': data.get('challenge')})
    
    # Check if the event is a message in the channel you're monitoring
    if 'channel' in event and event.get('channel') == 'CHANNEL-ID' and 'text' in event:
        user_message = event['text']
        thread_id = event.get('thread_ts') or event['ts']  # Thread timestamp

        # Prepare the assistant request
        assistant_request = {
            "assistant": assistant_id,
            "messages": [{"role": "user", "content": user_message}]
        }

        # Check for existing conversation state
        if thread_id in conversation_states:
            assistant_request["session_id"] = conversation_states[thread_id]

        try:
            # Send request to OpenAI Assistant
            response = openai.Assistant.create(**assistant_request)

            # Extract the assistant's response
            assistant_message = response['choices'][0]['message']['content']

            # Store or update the conversation state
            conversation_states[thread_id] = response['session_id']

            # Post the response back to the thread
            slack_client.chat_postMessage(channel=event['channel'], thread_ts=thread_id, text=assistant_message)

        except openai.error.OpenAIError as e:
            print(f"Error from OpenAI: {e}")
        except SlackApiError as e:
            print(f"Error posting message to Slack: {e}")

    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True)
