from flask import Flask, render_template, request, flash, redirect, url_for
import os
from model import read_resume_text, extract_skills_section, recommend_careers, df, vectorizer

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Needed for flash messages

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        flash("No file uploaded!", "error")
        return redirect(url_for("index"))

    file = request.files["resume"]
    if file.filename == "":
        flash("No selected file!", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type! Only PDF and DOCX are allowed.", "error")
        return redirect(url_for("index"))

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(file_path)

    try:
        resume_text = read_resume_text(file_path)
        
        if not resume_text:
            flash("Failed to extract text from the resume. Try another format!", "warning")
            return redirect(url_for("index"))

        skills_section = extract_skills_section(resume_text)

        if not skills_section:
            flash("No skills section found. Please check your resume format!", "warning")
            return redirect(url_for("index"))

        recommended_jobs = recommend_careers(skills_section, df, vectorizer)

        if recommended_jobs is None or recommended_jobs.empty:
            flash("No job recommendations found. Try updating your resume with more skills!", "info")
            return redirect(url_for("index"))

        return render_template("result.html", skills=skills_section, jobs=recommended_jobs.to_dict(orient="records"))

    except Exception as e:
        flash(f"Error processing resume: {e}", "error")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)

