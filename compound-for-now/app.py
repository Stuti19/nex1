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

# Add CORS headers after each request
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "https://www.compoundn.com"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Get the absolute path to the generated_reports directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
GENERATED_REPORTS_FOLDER = os.path.join(PROJECT_ROOT, "..", "public", "generated_reports")

# Ensure the generated_reports folder exists
os.makedirs(GENERATED_REPORTS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return jsonify({"message": "API is running"})

@app.route('/generate-report', methods=['POST', 'OPTIONS'])
def generate_report_endpoint():
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # Get the stock name from the request
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        stock_name = data.get('stock_name')
        print("Processing stock name:", stock_name)

        if not stock_name:
            return jsonify({"error": "Stock name is required"}), 400

        # Run the report generation logic
        try:
            asyncio.run(generate_report(stock_name))
        except Exception as e:
            print(f"Error in generate_report: {str(e)}")
            return jsonify({"error": f"Report generation failed: {str(e)}"}), 500

        # Generate the filename with timestamp
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{stock_name}_{date_str}_report.html"

        # Verify if the file exists
        report_path = os.path.join(GENERATED_REPORTS_FOLDER, filename)
        if not os.path.exists(report_path):
            print(f"Report file not found at: {report_path}")
            return jsonify({"error": "Report file not found"}), 404

        print(f"Report file found at: {report_path}")

        return jsonify({
            "message": "Report generated successfully",
            "filename": filename,
            "path": f"/generated_reports/{filename}"
        }), 200

    except Exception as e:
        print(f"Error in generate_report_endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/generated_reports/<path:filename>')
def serve_report(filename):
    try:
        print(f"Attempting to serve file: {filename}")
        print(f"Looking in directory: {GENERATED_REPORTS_FOLDER}")
        
        if not os.path.exists(os.path.join(GENERATED_REPORTS_FOLDER, filename)):
            print(f"File not found: {filename}")
            return jsonify({"error": "File not found"}), 404
            
        return send_from_directory(GENERATED_REPORTS_FOLDER, filename)
    except Exception as e:
        print(f"Error serving file: {str(e)}")
        return jsonify({"error": f"Error serving file: {str(e)}"}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
