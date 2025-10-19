from flask import Flask, render_template, request, redirect, url_for, send_file, session
from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key")  # for session

def to_list(s):
    if not s: return []
    raw = [x.strip() for x in s.replace(",", "\n").split("\n")]
    return [x for x in raw if x]

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        data = {
            "name": request.form.get("name", "").strip(),
            "title": request.form.get("title", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "location": request.form.get("location", "").strip(),
            "summary": request.form.get("summary", "").strip(),
            "skills": to_list(request.form.get("skills", "")),
            "experience": to_list(request.form.get("experience", "")),
            "education": to_list(request.form.get("education", "")),
            "projects": to_list(request.form.get("projects", "")),
            "links": to_list(request.form.get("links", "")),
        }
        session["resume"] = data
        return redirect(url_for("preview"))
    return render_template("form.html")

@app.route("/preview")
def preview():
    data = session.get("resume")
    if not data:
        return redirect(url_for("form"))
    return render_template("preview.html", r=data)

@app.route("/download.pdf")
def download_pdf():
    data = session.get("resume")
    if not data:
        return redirect(url_for("form"))

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    h1 = styles["Heading1"]; h2 = styles["Heading2"]; body = styles["BodyText"]

    # Header
    name_line = f"{data['name']}" if data["name"] else "Your Name"
    title_line = data["title"]
    contact_line = " | ".join([x for x in [data["email"], data["phone"], data["location"]] if x])
    story += [Paragraph(name_line, h1)]
    if title_line: story += [Paragraph(title_line, body)]
    if contact_line: story += [Paragraph(contact_line, body)]
    story += [Spacer(1, 12)]

    # Summary
    if data["summary"]:
        story += [Paragraph("Summary", h2), Paragraph(data["summary"], body), Spacer(1, 8)]

    # Skills grid
    if data["skills"]:
        story += [Paragraph("Skills", h2)]
        cols = 3
        rows = []
        items = data["skills"][:]
        while items:
            row = items[:cols]; items = items[cols:]
            row += [""] * (cols - len(row))
            rows.append(row)
        t = Table(rows, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("INNERGRID", (0,0), (-1,-1), 0.25, colors.grey),
            ("BOX", (0,0), (-1,-1), 0.25, colors.grey),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
        ]))
        story += [t, Spacer(1, 8)]

    # Reusable section adder
    def add_section(title, items):
        if items:
            story.append(Paragraph(title, h2))
            for it in items:
                story.append(Paragraph("• " + it, body))
            story.append(Spacer(1, 8))

    add_section("Experience", data["experience"])
    add_section("Projects", data["projects"])
    add_section("Education", data["education"])
    add_section("Links", data["links"])

    doc.build(story)
    buf.seek(0)
    return send_file(buf, as_attachment=True, download_name="resume.pdf", mimetype="application/pdf")

if __name__ == "__main__":
    app.run(debug=True)
