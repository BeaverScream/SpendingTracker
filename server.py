import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from uploader import upload_to_sheet

app = Flask(__name__)
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Use Flask's logger for app-specific logs
if not app.debug: # Ensure file logging in production, console in debug
    file_handler = logging.FileHandler('server.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(file_handler)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.info(f"Received /upload request. Form data: {request.form}")
    spreadsheet_id = request.form.get('spreadsheet_id')
    keyword = request.form.get('keyword')
    bankname = request.form.get('bankname')
    usertype_str = request.form.get('usertype')
    csv_file = request.files.get('csv_file')

    # File validation
    if not csv_file or csv_file.filename == '':
        app.logger.warning("CSV file is missing in the request.")
        return jsonify({"message": "CSV file is missing."}), 400

    # Parameter validation
    if not all([spreadsheet_id, keyword, bankname, usertype_str]):
        app.logger.warning("Missing one or more required form parameters.")
        return jsonify({"message": "Missing required form parameters (spreadsheet_id, keyword, bankname, usertype)."}), 400

    # usertype validation
    try:
        usertype = int(usertype_str)
    except ValueError:
        app.logger.warning(f"Invalid usertype provided: {usertype_str}")
        return jsonify({"message": "User type must be a valid integer."}), 400

    # bankname validation
    if not bankname or bankname.lower() not in ['tangerine', 'cibc']:
        app.logger.warning(f"Invalid bankname provided: {bankname}")
        return jsonify({"message": "Invalid bank name. Must be 'tangerine' or 'cibc'."}), 400

    filepath = None
    try:
        filename = secure_filename(csv_file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        csv_file.save(filepath)
        app.logger.info(f"Temporary file saved at {filepath}")

        keyfile_path = 'sample-25a27-e4c1004f429c.json'

        app.logger.info(f"Calling upload_to_sheet with: sheet_id='{spreadsheet_id}', keyword='{keyword}', bank='{bankname}', user_type='{usertype}'")
        upload_to_sheet(spreadsheet_id, keyword, filepath, bankname, usertype, keyfile_path)
        app.logger.info("upload_to_sheet completed successfully.")

        return jsonify({"message": "File uploaded and processed successfully!"})

    except Exception as e:
        app.logger.error("Error during upload process:", exc_info=True)
        return jsonify({"message": "An error occurred during processing."}), 500
    finally:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            app.logger.info(f"Temporary file {filepath} deleted.")

if __name__ == '__main__':
    # Ensure app.logger is used after it might have handlers added
    if not app.debug:
        app.logger.info("Flask server started in production mode.")
    else:
        app.logger.info("Flask server started in debug mode.")
    app.run(debug=True)
