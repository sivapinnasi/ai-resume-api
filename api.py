from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import os
import base64
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY not found. Set it in Render's environment variables.")

# Resume templates
TEMPLATES = {
    "professional": {
        "font": "Calibri",
        "heading_size": 14,
        "subheading_size": 12,
        "body_size": 11,
        "heading_color": "2F5496",
        "use_borders": True
    },
    "creative": {
        "font": "Georgia",
        "heading_size": 16,
        "subheading_size": 13,
        "body_size": 12,
        "heading_color": "7A1712",
        "use_borders": False
    },
    "minimal": {
        "font": "Arial",
        "heading_size": 13,
        "subheading_size": 11,
        "body_size": 10,
        "heading_color": "000000",
        "use_borders": False
    }
}

def generate_resume_content(user_data):
    prompt = f"""
    Create a professional resume for a {user_data['job_title']} role with the following information:
    
    Skills: {', '.join(user_data['skills'])}
    Certificates: {', '.join(user_data['certificates'])}
    Projects: {', '.join(user_data['projects'])}
    Education: {user_data['education']}
    Work experience: {user_data['experience']}
    
    Format in JSON with these fields:
    - summary
    - skills
    - experience
    - education
    - projects
    - certificates
    """

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "anthropic/claude-3-opus",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            }
        )

        if response.status_code == 200:
            result = response.json()
            return json.loads(result["choices"][0]["message"]["content"])
        else:
            logger.error(f"OpenRouter API error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        logger.exception(f"Error generating content: {e}")
        return None

def create_docx_resume(user_data, ai_content, template_name):
    template = TEMPLATES.get(template_name, TEMPLATES["professional"])
    
    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    doc.add_heading(user_data['name'], level=0).alignment = WD_ALIGN_PARAGRAPH.CENTER

    contact_info = doc.add_paragraph()
    contact_info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact_info.add_run(f"{user_data['email']} | {user_data['phone']} | {user_data['address']}")

    doc.add_heading('Professional Summary', level=1)
    doc.add_paragraph(ai_content['summary'])

    doc.add_heading('Skills', level=1)
    doc.add_paragraph(ai_content['skills'])

    doc.add_heading('Professional Experience', level=1)
    doc.add_paragraph(ai_content['experience'])

    doc.add_heading('Education', level=1)
    doc.add_paragraph(ai_content['education'])

    doc.add_heading('Projects', level=1)
    doc.add_paragraph(ai_content['projects'])

    doc.add_heading('Certifications', level=1)
    doc.add_paragraph(ai_content['certificates'])

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io.getvalue()

@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    try:
        data = request.get_json()
        required = ['name', 'email', 'phone', 'address', 'job_title', 
                    'skills', 'certificates', 'projects', 'education', 
                    'experience', 'template']

        missing = [field for field in required if field not in data]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        if data['template'] not in TEMPLATES:
            return jsonify({"error": "Invalid template"}), 400

        ai_content = generate_resume_content(data)
        if not ai_content:
            return jsonify({"error": "Failed to generate content"}), 500

        resume_bytes = create_docx_resume(data, ai_content, data['template'])
        resume_base64 = base64.b64encode(resume_bytes).decode('utf-8')

        return jsonify({
            "success": True,
            "resume": resume_base64,
            "filename": f"{data['name'].replace(' ', '_')}_resume.docx"
        })

    except Exception as e:
        logger.exception("Unhandled error")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
