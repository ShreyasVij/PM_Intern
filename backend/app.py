from flask import Flask, request, jsonify
import csv

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World! Flask is running!'

import json

def save_profile(profile_data):
    """Saves a new profile to the profiles.json file."""
    # try:
    #     # Load existing profiles
    #     with open('data/profiles.json', 'r') as f:
    #         profiles = json.load(f)
    # except (FileNotFoundError, json.JSONDecodeError):
    #     # Handle the case where the file is new or empty
    #     profiles = []

    # # Add the new profile to the list
    # profiles.append(profile_data)

    # # Save the updated list back to the file
    # with open('data/profiles.json', 'w') as f:
    #     json.dump(profiles, f, indent=4)

    # return True

@app.route('/api/profile', methods=['POST'])
def receive_profile():
    #will get data from here
    profile_data = request.get_json()
    if not profile_data:
        return jsonify({"error": "No data received"}), 400  # Return a bad request error

    # 3. Save the profile data
    if save_profile(profile_data):
        return jsonify({"message": "Profile saved successfully"}), 201 # Return a success message
    else:
        return jsonify({"error": "Failed to save profile"}), 500

@app.route("/api/internships", methods=["GET"])
def display_internships():
    """Reads internships.csv and returns it as JSON"""
    internships = []

    try:
        with open('data/internships.csv', mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                internships.append(row)

        return jsonify({"internships": internships}), 200  # Success response

    except FileNotFoundError:
        return jsonify({"error": "internships.csv not found"}), 404

    except Exception as e:
        return jsonify({"error": f"Failed to load internships: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=3000)