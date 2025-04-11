import subprocess
import time
from flask import Flask, request, jsonify
import requests
from PIL import Image, ImageChops
import base64
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

class VLMAgent:
    def __init__(self, api_key):
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def analyze_screenshot(self, image_path, prompt):
        with open(image_path, "rb") as img_file:
            base64_image = base64.b64encode(img_file.read()).decode('utf-8')
        
        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ]
            }],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logging.error(f"VLM API error: {str(e)}")
            return None

class ActionExecutor:
    @staticmethod
    def execute_action(action):
        try:
            if action.startswith("KEY_"):
                subprocess.run(["ydotool", "key", "--key-delay", "100", action[4:]])
            elif action.startswith("CLICK_"):
                x, y = action[6:].split(",")
                subprocess.run(["ydotool", "mousemove", "--", x, y])
                subprocess.run(["ydotool", "click", "0xC0"])
            elif action.startswith("TYPE_"):
                text = action[5:].replace(" ", "space")
                subprocess.run(["ydotool", "type", "--key-delay", "50", text])
            return True
        except Exception as e:
            logging.error(f"Action failed: {str(e)}")
            return False

def capture_screenshot(output_path="screenshot.png"):
    try:
        subprocess.run(
            f"grim -g \"$(slurp)\" {output_path}",
            shell=True,
            check=True,
            executable="/bin/bash"
        )
        return True
    except subprocess.CalledProcessError:
        return False

def compare_images(img1_path, img2_path):
    with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
        diff = ImageChops.difference(img1, img2)
        return diff.getbbox() is None

@app.route('/execute', methods=['POST'])
def execute_task():
    data = request.json
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "API key missing"}), 400
    
    agent = VLMAgent(api_key)
    executor = ActionExecutor()
    max_attempts = 5
    attempt = 0
    prev_screenshot = None
    
    while attempt < max_attempts:
        attempt += 1
        current_screenshot = f"screenshot_{attempt}.png"
        
        if not capture_screenshot(current_screenshot):
            return jsonify({"error": "Failed to capture screenshot"}), 500
            
        if prev_screenshot and compare_images(prev_screenshot, current_screenshot):
            return jsonify({"error": "No state change detected"}), 400
            
        response = agent.analyze_screenshot(current_screenshot, data['prompt'])
        if not response or "ACTION:" not in response:
            return jsonify({"error": "Invalid VLM response"}), 500
            
        action = response.split("ACTION:")[1].strip()
        if not executor.execute_action(action):
            return jsonify({"error": "Action execution failed"}), 500
            
        prev_screenshot = current_screenshot
        time.sleep(1)
    
    return jsonify({"error": "Max attempts reached"}), 400

def main():
    app.run(host='0.0.0.0', port=5000)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
