from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import os
from main import main as generate_report
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Get allowed origins from environment variable, fallback to localhost if not set
default_origins = 'http://localhost:3000,https://nex1-seven.vercel.app'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', default_origins).split(',')

# Configure CORS with the origins from environment variable
CORS(app, resources={
    r"/*": {
        "origins": ALLOWED_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Get the absolute path to the Nex/public/generated_reports directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GENERATED_REPORTS_FOLDER = os.path.join(PROJECT_ROOT, "..", "public", "generated_reports")

# Ensure the generated_reports folder exists
os.makedirs(GENERATED_REPORTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return jsonify({"message": "API is running"})

@app.route('/generate-report', methods=['POST'])
def generate_report_endpoint():
    try:
        # Get the stock name from the request
        data = request.json
        stock_name = data.get('stock_name')

        if not stock_name:
            return jsonify({"error": "Stock name is required"}), 400

        # Run the report generation logic
        asyncio.run(generate_report(stock_name))

        # Generate the filename with timestamp
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{stock_name}_{date_str}_report.html"

        # Verify if the file exists
        report_path = os.path.join(GENERATED_REPORTS_FOLDER, filename)
        if not os.path.exists(report_path):
            print(f"Report file not found at: {report_path}")  # Debug log
            return jsonify({"error": "Report file not found"}), 404

        print(f"Report file found at: {report_path}")  # Debug log

        # Return the path to the generated report
        return jsonify({
            "message": "Report generated successfully",
            "filename": filename,
            "path": f"/generated_reports/{filename}"
        }), 200

    except Exception as e:
        print(f"Error generating report: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.route('/generated_reports/<path:filename>')
def serve_report(filename):
    try:
        print(f"Attempting to serve file: {filename}")  # Debug log
        print(f"Looking in directory: {GENERATED_REPORTS_FOLDER}")  # Debug log
        
        if not os.path.exists(os.path.join(GENERATED_REPORTS_FOLDER, filename)):
            print(f"File not found: {filename}")  # Debug log
            return jsonify({"error": "File not found"}), 404
            
        return send_from_directory(GENERATED_REPORTS_FOLDER, filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")  # Debug log
        return jsonify({"error": f"Error serving file: {str(e)}"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
