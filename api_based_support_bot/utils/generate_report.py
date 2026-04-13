from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
import os

def create_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = styles['Title']
    h1_style = styles['Heading1']
    h2_style = styles['Heading2']
    body_style = styles['BodyText']
    bullet_style = ParagraphStyle('Bullet', parent=styles['BodyText'], leftIndent=20, bulletIndent=10)

    # 1. Title
    story.append(Paragraph("Technical Proposal & Cost Optimization Report: FYJC Student Chatbot", title_style))
    story.append(Spacer(1, 12))

    # 2. Section 1 - Context
    story.append(Paragraph("1. Project Context", h2_style))
    story.append(Paragraph("<b>Target Audience:</b> 1.5 Million (15 Lakh) Students in Maharashtra.", body_style))
    story.append(Paragraph("<b>Expected Volume:</b> 4.5 to 5 Million queries per admission cycle.", body_style))
    story.append(Paragraph("<b>Objective:</b> Provide high-accuracy, low-latency support for FYJC admissions while maintaining fiscal efficiency.", body_style))
    story.append(Spacer(1, 12))

    # 3. Section 2 - Comparison
    story.append(Paragraph("2. Comparison: API vs. Self-Hosted Server", h2_style))
    story.append(Paragraph("<u>Option A: API-Based Server (Llama 3.1 8B via Groq)</u>", h2_style))
    story.append(Paragraph("Used for initial testing and rapid deployment.", body_style))
    story.append(Paragraph("• <b>Accuracy:</b> Moderate (8B-class model).", bullet_style))
    story.append(Paragraph("• <b>Cost:</b> $0.05 / 1M Input, $0.08 / 1M Output tokens.", bullet_style))
    story.append(Paragraph("• <b>Total Cycle Cost:</b> ~$540 (~₹45,000).", bullet_style))
    story.append(Paragraph("• <b>Scalability Risk:</b> Limited by Tokens Per Minute (TPM) caps.", bullet_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("<u>Option B: Dedicated Self-Hosted Server (IBM Granite 4.0 on NVIDIA L40S)</u>", h2_style))
    
    # Try to add image if exists
    img_path = "/Users/apple/.gemini/antigravity/brain/28b1c3e3-374c-421b-a137-29d5f0e9f945/artifacts/gpu_pricing.png"
    if os.path.exists(img_path):
        try:
            img = Image(img_path, width=400, height=300)
            story.append(img)
            story.append(Spacer(1, 12))
        except:
            pass

    story.append(Paragraph("• <b>Accuracy:</b> High (30B-class reasoning).", bullet_style))
    story.append(Paragraph("• <b>Cost:</b> Fixed ₹50,000 per month (Local Indian Vendor).", bullet_style))
    story.append(Paragraph("• <b>Scalability Benefit:</b> Unlimited Tokens via vLLM optimization.", bullet_style))
    story.append(Spacer(1, 12))

    # 4. Section 3 - Granite Advantage
    story.append(Paragraph("3. The IBM Granite 4.0 Advantage", h2_style))
    story.append(Paragraph("1. <b>Memory Compression:</b> Reduces KV cache usage by 70% vs traditional transformers.", body_style))
    story.append(Paragraph("2. <b>vLLM Efficiency:</b> Allows massive batching on L40S GPU.", body_style))
    story.append(Paragraph("3. <b>Speed:</b> Hybrid Mamba-2 architecture allows 2x faster latency.", body_style))
    story.append(Spacer(1, 12))

    # 5. Section 4 - Redis
    story.append(Paragraph("4. Cost Mitigation via Redis Semantic Caching", h2_style))
    story.append(Paragraph("Implementing a Semantic Cache reduces LLM calls by 30% to 50% by serving identical or similar queries from memory.", body_style))
    story.append(Spacer(1, 12))

    # 6. Table
    story.append(Paragraph("5. Summary Analysis", h2_style))
    data = [
        ['Feature', 'API-Based (8B)', 'Self-Hosted (L40S + Granite)'],
        ['Reasoning', 'Standard', 'Advanced (32B Level)'],
        ['Concurrency', 'Low (Rate Limited)', 'Extreme (vLLM/FP8)'],
        ['Cost (Monthly)', '~₹45,000', '₹50,000 (Fixed)']
    ]
    t = Table(data, colWidths=[120, 160, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(t)
    story.append(Spacer(1, 24))

    story.append(Paragraph("Final Recommendation: Optimized Self-Hosting (L40S + Granite 4.0)", h1_style))

    # Build PDF
    doc.build(story)
    print(f"Report generated successfully: {filename}")

if __name__ == "__main__":
    create_pdf("FINAL_SUBMISSION_REPORT.pdf")
