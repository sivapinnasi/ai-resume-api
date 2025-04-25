from fastapi import FastAPI
from pydantic import BaseModel
import os
from docx import Document
from fastapi.responses import FileResponse

app = FastAPI()

class ResumeData(BaseModel):
    name: str
    address: str
    phone: str
    email: str
    experience: str
    projects: str
    certificates: str
    education: str
    skills: str
    template_name: str

@app.post("/generate-resume")
async def generate_resume(data: ResumeData):
    # Create the resume document
    doc = Document()
    doc.add_heading(f"Resume for {data.name}", 0)
    
    doc.add_paragraph(f"Name: {data.name}")
    doc.add_paragraph(f"Address: {data.address}")
    doc.add_paragraph(f"Phone: {data.phone}")
    doc.add_paragraph(f"Email: {data.email}")
    doc.add_paragraph(f"Experience: {data.experience}")
    doc.add_paragraph(f"Projects: {data.projects}")
    doc.add_paragraph(f"Certificates: {data.certificates}")
    doc.add_paragraph(f"Education: {data.education}")
    doc.add_paragraph(f"Skills: {data.skills}")

    # Save the document to a file
    filename = f"{data.name}_resume.docx"
    file_path = os.path.join("resumes", filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc.save(file_path)
    
    # Return the file path for download
    return {"download_url": f"/download/{filename}"}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join("resumes", filename)
    return FileResponse(file_path)
