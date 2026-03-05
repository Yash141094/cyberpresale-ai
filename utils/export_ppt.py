"""
PowerPoint export for CyberPresales AI
Generates a professional presentation from analysis results
"""
import os
import tempfile
from datetime import datetime

def generate_ppt(session_state):
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt, Emu
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "python-pptx", "--break-system-packages", "-q"])
        from pptx import Presentation
        from pptx.util import Inches, Pt, Emu
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN

    # Colors
    NAVY    = RGBColor(0x1e, 0x29, 0x3b)
    BLUE    = RGBColor(0x1e, 0x40, 0xaf)
    ACCENT  = RGBColor(0x3b, 0x82, 0xf6)
    WHITE   = RGBColor(0xff, 0xff, 0xff)
    LIGHT   = RGBColor(0xe2, 0xe8, 0xf0)
    GRAY    = RGBColor(0x94, 0xa3, 0xb8)
    GREEN   = RGBColor(0x10, 0xb9, 0x81)
    AMBER   = RGBColor(0xf5, 0x9e, 0x0b)

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]  # blank

    def get(key):
        if hasattr(session_state, key):
            return getattr(session_state, key)
        if hasattr(session_state, '__getitem__'):
            return session_state.get(key)
        return None

    def add_rect(slide, x, y, w, h, color, alpha=None):
        from pptx.util import Inches
        shape = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
        return shape

    def add_textbox(slide, x, y, w, h, text, font_size=14, color=WHITE, bold=False,
                    align=PP_ALIGN.LEFT, italic=False, font_name="Calibri"):
        txBox = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size)
        run.font.color.rgb = color
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font_name
        return txBox

    def truncate(text, max_chars=600):
        if not text:
            return "Analysis not yet generated."
        # Clean markdown
        lines = []
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('## ') or line.startswith('### '):
                line = line.lstrip('#').strip()
            if line.startswith('**') and line.endswith('**'):
                line = line.strip('*')
            if line:
                lines.append(line)
        cleaned = '\n'.join(lines)
        if len(cleaned) > max_chars:
            return cleaned[:max_chars] + '...'
        return cleaned

    def add_bullet_slide(title, content, subtitle=None, accent_color=ACCENT):
        slide = prs.slides.add_slide(blank_layout)

        # Dark background
        add_rect(slide, 0, 0, 13.33, 7.5, NAVY)

        # Left accent bar
        add_rect(slide, 0, 0, 0.08, 7.5, accent_color)

        # Top strip
        add_rect(slide, 0.08, 0, 13.25, 1.1, RGBColor(0x0f, 0x17, 0x2a))

        # Title
        add_textbox(slide, 0.3, 0.15, 10, 0.8, title,
                    font_size=24, bold=True, color=WHITE, font_name="Calibri")

        if subtitle:
            add_textbox(slide, 0.3, 0.82, 10, 0.3, subtitle,
                        font_size=11, color=GRAY, font_name="Calibri", italic=True)

        # Content area
        add_textbox(slide, 0.3, 1.25, 12.7, 6.0, truncate(content, 800),
                    font_size=13, color=LIGHT, font_name="Calibri")

        # Page label
        add_textbox(slide, 11.5, 7.0, 1.7, 0.35,
                    f"CyberPresales AI · {datetime.now().strftime('%b %Y')}",
                    font_size=8, color=GRAY, align=PP_ALIGN.RIGHT)

        return slide

    # ── Slide 1: Cover ────────────────────────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, NAVY)
    add_rect(slide, 0, 0, 13.33, 0.06, ACCENT)
    add_rect(slide, 0, 7.44, 13.33, 0.06, ACCENT)
    add_rect(slide, 0, 0, 0.06, 7.5, ACCENT)

    # Big title
    add_textbox(slide, 1.5, 1.5, 10, 1.2, "CYBERSECURITY PROPOSAL",
                font_size=36, bold=True, color=WHITE, align=PP_ALIGN.CENTER, font_name="Calibri")
    add_textbox(slide, 1.5, 2.7, 10, 0.6, "Presales Intelligence Report",
                font_size=20, color=ACCENT, align=PP_ALIGN.CENTER, font_name="Calibri")

    file_name = get('file_name') or 'RFP Document'
    add_textbox(slide, 1.5, 3.5, 10, 0.5, f"Document: {file_name}",
                font_size=14, color=GRAY, align=PP_ALIGN.CENTER, font_name="Calibri")
    add_textbox(slide, 1.5, 4.1, 10, 0.4, f"Generated: {datetime.now().strftime('%B %d, %Y')}",
                font_size=12, color=GRAY, align=PP_ALIGN.CENTER, font_name="Calibri")

    # Stats row
    modules_run = sum(1 for k in ["customer_brief","pain_analysis","solution_rec","competitive","product_map","exec_summary"] if get(k))
    stats = [
        ("Modules Run", str(modules_run)),
        ("Platform", "CyberPresales AI v3"),
        ("Author", "Yash Mehrotra"),
    ]
    x_start = 2.0
    for label, val in stats:
        add_rect(slide, x_start, 5.2, 2.8, 1.0, RGBColor(0x1e, 0x40, 0xaf))
        add_textbox(slide, x_start+0.1, 5.3, 2.6, 0.45, val,
                    font_size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_textbox(slide, x_start+0.1, 5.75, 2.6, 0.35, label,
                    font_size=9, color=LIGHT, align=PP_ALIGN.CENTER)
        x_start += 3.1

    # ── Slide 2: Table of Contents ────────────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, NAVY)
    add_rect(slide, 0, 0, 0.08, 7.5, GREEN)
    add_rect(slide, 0.08, 0, 13.25, 1.1, RGBColor(0x0f, 0x17, 0x2a))
    add_textbox(slide, 0.3, 0.15, 10, 0.8, "Contents",
                font_size=26, bold=True, color=WHITE, font_name="Calibri")

    sections = [
        ("01", "Executive Summary", bool(get('exec_summary'))),
        ("02", "Customer Intelligence Brief", bool(get('customer_brief'))),
        ("03", "Pain Point Analysis", bool(get('pain_analysis'))),
        ("04", "Solution Recommendation", bool(get('solution_rec'))),
        ("05", "Competitive Landscape", bool(get('competitive'))),
        ("06", "Product & Vendor Mapping", bool(get('product_map'))),
    ]

    y = 1.3
    for num, name, done in sections:
        col = GREEN if done else GRAY
        add_rect(slide, 0.3, y, 0.5, 0.5, col)
        add_textbox(slide, 0.3, y+0.08, 0.5, 0.35, num,
                    font_size=12, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
        add_textbox(slide, 1.0, y+0.08, 8, 0.38, name,
                    font_size=14, color=WHITE if done else GRAY, bold=done)
        status = "✓ Generated" if done else "Pending"
        add_textbox(slide, 10.5, y+0.08, 2.5, 0.38, status,
                    font_size=11, color=GREEN if done else GRAY, align=PP_ALIGN.RIGHT)
        y += 0.7

    # ── Slide 3: Executive Summary ────────────────────────────────────────────
    if get('exec_summary'):
        add_bullet_slide("Executive Summary",
                         get('exec_summary'),
                         "Board-ready proposal narrative for C-level stakeholders",
                         accent_color=ACCENT)

    # ── Slide 4: Customer Brief ───────────────────────────────────────────────
    if get('customer_brief'):
        add_bullet_slide("Customer Intelligence Brief",
                         get('customer_brief'),
                         "Who they are · Why this RFP · Key decision makers",
                         accent_color=GREEN)

    # ── Slide 5: Pain Analysis ────────────────────────────────────────────────
    if get('pain_analysis'):
        add_bullet_slide("Pain Point Analysis",
                         get('pain_analysis'),
                         "Surface requirements vs underlying business pains",
                         accent_color=AMBER)

    # ── Slide 6: Solution Recommendation ─────────────────────────────────────
    if get('solution_rec'):
        add_bullet_slide("Solution Recommendation",
                         get('solution_rec'),
                         "What to propose · Architecture approach · POC strategy",
                         accent_color=ACCENT)

    # ── Slide 7: Competitive Landscape ───────────────────────────────────────
    if get('competitive'):
        add_bullet_slide("Competitive Intelligence",
                         get('competitive'),
                         "Likely competitors · Where we win · Counter-strategy",
                         accent_color=RGBColor(0xec, 0x48, 0x99))

    # ── Slide 8: Product Mapping ──────────────────────────────────────────────
    if get('product_map'):
        add_bullet_slide("Product & Vendor Recommendations",
                         get('product_map'),
                         "Domain-by-domain · Primary & alternative vendors · Deal strategy",
                         accent_color=RGBColor(0x8b, 0x5c, 0xf6))

    # ── Slide 9: Closing ──────────────────────────────────────────────────────
    slide = prs.slides.add_slide(blank_layout)
    add_rect(slide, 0, 0, 13.33, 7.5, NAVY)
    add_rect(slide, 0, 0, 13.33, 0.06, ACCENT)
    add_rect(slide, 0, 7.44, 13.33, 0.06, ACCENT)

    add_textbox(slide, 1.5, 2.0, 10, 1.0, "Ready to Win This Deal?",
                font_size=32, bold=True, color=WHITE, align=PP_ALIGN.CENTER, font_name="Calibri")
    add_textbox(slide, 1.5, 3.1, 10, 0.6,
                "This analysis was generated by CyberPresales AI",
                font_size=16, color=ACCENT, align=PP_ALIGN.CENTER)
    add_textbox(slide, 1.5, 3.8, 10, 0.5,
                "Built by Yash Mehrotra · Powered by Groq LLaMA 3.3 · v3.0",
                font_size=12, color=GRAY, align=PP_ALIGN.CENTER)

    # Save
    output_path = os.path.join(tempfile.gettempdir(), "CyberPresales_Presentation.pptx")
    prs.save(output_path)
    return output_path
