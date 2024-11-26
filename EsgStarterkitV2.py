import streamlit as st
from openai import OpenAI
import json
import datetime
import io
import os
import re
import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    Table, TableStyle, Image, NextPageTemplate,
    PageTemplate, Frame
)
from reportlab.lib.pagesizes import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Image, Frame
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.enums import TA_CENTER
import io
import os
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, PageTemplate, Frame, PageBreak, Image, Paragraph, NextPageTemplate
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
# Constants
FIELDS_OF_INDUSTRY = [
    "Agriculture", "Forestry", "Fishing", "Mining and Quarrying",
    "Oil and Gas Exploration", "Automotive", "Aerospace",
    "Electronics", "Textiles and Apparel", "Food and Beverage Manufacturing",
    "Steel and Metalworking", "Construction and Infrastructure",
    "Energy and Utilities", "Chemical Production",
    "Banking and Financial Services", "Insurance", "Retail and E-commerce",
    "Tourism and Hospitality", "Transportation and Logistics",
    "Real Estate and Property Management", "Healthcare and Pharmaceuticals",
    "Telecommunications", "Media and Entertainment", "Others"
]

ORGANIZATION_TYPES = [
    "Public Listed Company",
    "Financial Institution",
    "SME/Enterprise",
    "Government Agency",
    "NGO",
    "Others"
]

ESG_READINESS_QUESTIONS = {
    "1. Have you started formal ESG initiatives within your organization?": [
        "No, we haven't started yet.",
        "Yes, we've started basic efforts but lack a structured plan.",
        "Yes, we have a formalized ESG framework in place.",
        "Yes, we are actively implementing and reporting ESG practices."
    ],
    "2. What is your primary reason for considering ESG initiatives?": [
        "To comply with regulations and avoid penalties.",
        "To improve reputation and meet stakeholder demands.",
        "To attract investors or access green funding.",
        "To align with broader sustainability and ethical goals."
    ],
    "3. Do you have a team or individual responsible for ESG in your organization?": [
        "No, there is no one currently assigned to ESG matters.",
        "Yes, but they are not exclusively focused on ESG.",
        "Yes, we have a dedicated ESG team or officer.",
        "Yes, and we also involve external advisors for support."
    ],
    "4. Are you aware of the ESG standards relevant to your industry?": [
        "No, I am unfamiliar with industry-specific ESG standards.",
        "I've heard of them but don't fully understand how to apply them.",
        "Yes, I am somewhat familiar and have started researching.",
        "Yes, and we have begun aligning our operations with these standards."
    ],
    "5. Do you currently measure your environmental or social impacts?": [
        "No, we have not started measuring impacts.",
        "Yes, we measure basic indicators (e.g., waste, energy use).",
        "Yes, we track a range of metrics but need a better system.",
        "Yes, we have comprehensive metrics with detailed reports."
    ],
    "6. What is your biggest challenge in starting or scaling ESG initiatives?": [
        "Lack of knowledge and expertise.",
        "Insufficient budget and resources.",
        "Difficulty aligning ESG goals with business priorities.",
        "Regulatory complexity and compliance requirements."
    ]
}
class PDFWithTOC(SimpleDocTemplate):
    def __init__(self, *args, **kwargs):
        SimpleDocTemplate.__init__(self, *args, **kwargs)
        self.page_numbers = {}
        self.current_page = 1

    def afterPage(self):
        self.current_page += 1

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):
            style = flowable.style.name
            if style == 'heading':
                text = flowable.getPlainText()
                self.page_numbers[text] = self.current_page

def generate_pdf(esg_data, personal_info, toc_page_numbers):
    buffer = io.BytesIO()
    
    doc = PDFWithTOC(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=1.5*inch,
        bottomMargin=inch
    )
    
    full_page_frame = Frame(
        0, 0, letter[0], letter[1],
        leftPadding=0, rightPadding=0,
        topPadding=0, bottomPadding=0
    )
    
    normal_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    disclaimer_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='disclaimer'
    )
    
    templates = [
        PageTemplate(id='First', frames=[full_page_frame],
                    onPage=lambda canvas, doc: None),
        PageTemplate(id='Later', frames=[normal_frame],
                    onPage=create_header_footer),
        PageTemplate(id='dis', frames=[normal_frame],
                    onPage=create_header_footer_disclaimer)
    ]
    doc.addPageTemplates(templates)
    
    styles = create_custom_styles()
    
    # TOC style with right alignment for page numbers
    toc_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['normal'],
        fontSize=12,
        leading=20,
        leftIndent=20,
        rightIndent=30,
        spaceBefore=10,
        spaceAfter=10,
        fontName='Helvetica'
    )
    styles['toc'] = toc_style
    
    elements = []
    
    # Cover page
    elements.append(NextPageTemplate('First'))
    if os.path.exists("frontemma.jpg"):
        img = Image("frontemma.jpg", width=letter[0], height=letter[1])
        elements.append(img)
    
    elements.append(NextPageTemplate('Later'))
    elements.append(PageBreak())
    elements.append(Paragraph("Table of Contents", styles['heading']))
    
    # Section data
    section_data = [
        ("ESG Initial Assessment", esg_data['analysis1']),
        ("Framework Analysis", esg_data['analysis2']),
        ("Management Issues", esg_data['management_questions']),
        ("Implementation Challenges", esg_data['implementation_challenges']),
        ("Advisory Plan", esg_data['advisory']),
        ("SROI Analysis", esg_data['sroi'])
    ]
    
    # Format TOC entries with dots and manual page numbers
    def create_toc_entry(num, title, page_num):
        title_with_num = f"{num}. {title}"
        dots = '.' * (50 - len(title_with_num))
        return f"{title_with_num} {dots} {page_num}"

    # First add the static Executive Summary entry
    static_entry = create_toc_entry(1, "Profile Analysis", 3)  # 3 is the page number
    elements.append(Paragraph(static_entry, toc_style))

    # Then continue with the dynamic entries, starting from number 2
    for i, ((title, _), page_num) in enumerate(zip(section_data, toc_page_numbers), 2):
        toc_entry = create_toc_entry(i, title, page_num)
        elements.append(Paragraph(toc_entry, toc_style))
    
    elements.append(PageBreak())
    
    # Content pages
    elements.extend(create_second_page(styles, personal_info))
    elements.append(PageBreak())
    
    # Main content
    for i, (title, content) in enumerate(section_data):
        elements.append(Paragraph(title, styles['heading']))
        process_content(content, styles, elements)
        if i < len(section_data) - 1:
            elements.append(PageBreak())
    
    # Disclaimer
    elements.append(NextPageTemplate('dis'))
    elements.append(PageBreak())
    create_disclaimer_page(styles, elements)
    
    # Back cover
    elements.append(NextPageTemplate('First'))
    elements.append(PageBreak())
    if os.path.exists("backemma.png"):
        img = Image("backemma.png", width=letter[0], height=letter[1])
        elements.append(img)
    
    doc.build(elements, canvasmaker=NumberedCanvas)
    buffer.seek(0)
    return buffer

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        if hasattr(self, '_pageNumber'):
            self.setFont("Helvetica", 9)



def create_disclaimer_page(styles, elements):
    """Create a single-page disclaimer using Lato font family"""
    
    # Register Lato fonts
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    # Define custom styles for the disclaimer page with Lato
    disclaimer_styles = {
        'title': ParagraphStyle(
            'DisclaimerTitle',
            parent=styles['normal'],
            fontSize=24,
            fontName=bold_font,
            leading=28,
            spaceBefore=0,
            spaceAfter=10,
        ),
        'section_header': ParagraphStyle(
            'SectionHeader',
            parent=styles['normal'],
            fontSize=10,
            fontName=bold_font,
            leading=13,
            spaceBefore=2,
            spaceAfter=3,
        ),
        'body_text': ParagraphStyle(
            'BodyText',
            parent=styles['normal'],
            fontSize=8,
            fontName=base_font,
            leading=10,
            spaceBefore=1,
            spaceAfter=3,
            alignment=TA_JUSTIFY,
        ),
        'item_header': ParagraphStyle(
            'ItemHeader',
            parent=styles['normal'],
            fontSize=8,
            fontName=bold_font,
            leading=11,
            spaceBefore=4,
            spaceAfter=1,
        ),
        'confidential': ParagraphStyle(
            'Confidential',
            parent=styles['normal'],
            fontSize=8,
            fontName=base_font,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceBefore=1,
        )
    }    
    # Main Content
    elements.append(Paragraph("Limitations of AI in Financial and Strategic Evaluations", 
                            disclaimer_styles['section_header']))

    # AI Limitations Section
    limitations = [
        ("1. Data Dependency and Quality",
         "AI models rely heavily on the quality and completeness of the data fed into them. The accuracy of the analysis is contingent upon the integrity of the input data. Inaccurate, outdated, or incomplete data can lead to erroneous conclusions and recommendations. Users should ensure that the data used in AI evaluations is accurate and up-to-date."),
        
        ("2. Algorithmic Bias and Limitations",
         "AI algorithms are designed based on historical data and predefined models. They may inadvertently incorporate biases present in the data, leading to skewed results. Additionally, AI models might not fully capture the complexity and nuances of human behavior or unexpected market changes, potentially impacting the reliability of the analysis."),
        
        ("3. Predictive Limitations",
         "While AI can identify patterns and trends, it cannot predict future events with certainty. Financial markets and business environments are influenced by numerous unpredictable factors such as geopolitical events, economic fluctuations, and technological advancements. AI's predictions are probabilistic and should not be construed as definitive forecasts."),
        
        ("4. Interpretation of Results",
         "AI-generated reports and analyses require careful interpretation. The insights provided by AI tools are based on algorithms and statistical models, which may not always align with real-world scenarios. It is essential to involve human expertise in interpreting AI outputs and making informed decisions."),
        
        ("5. Compliance and Regulatory Considerations",
         "The use of AI in financial evaluations and business strategy formulation must comply with relevant regulations and standards. Users should be aware of legal and regulatory requirements applicable to AI applications in their jurisdiction and ensure that their use of AI tools aligns with these requirements.")
    ]

    for title, content in limitations:
        elements.append(Paragraph(title, disclaimer_styles['item_header']))
        elements.append(Paragraph(content, disclaimer_styles['body_text']))

    # RAA Capital Partners Section
    elements.append(Paragraph("RAA Capital Partners Sdn Bhd and Advisory Partners' Disclaimer",
                            disclaimer_styles['section_header']))

    elements.append(Paragraph(
        "RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners provide AI-generated reports and insights as a tool to assist in financial and business strategy evaluations. However, the use of these AI-generated analyses is subject to the following disclaimers:",
        disclaimer_styles['body_text']
    ))

    disclaimers = [
        ("1. No Guarantee of Accuracy or Completeness",
         "While RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners strive to ensure that the AI-generated reports and insights are accurate and reliable, we do not guarantee the completeness or accuracy of the information provided. The insights are based on the data and models used, which may not fully account for all relevant factors or changes in the market."),
        
        ("2. Not Financial or Professional Advice",
         "The AI-generated reports and insights are not intended as financial, investment, legal, or professional advice. Users should consult with qualified professionals before making any financial or strategic decisions based on AI-generated reports. RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners are not responsible for any decisions made based on the reports provided."),
        
        ("3. Limitation of Liability",
         "RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners shall not be liable for any loss or damage arising from the use of AI-generated reports and insights. This includes, but is not limited to, any direct, indirect, incidental, or consequential damages resulting from reliance on the reports or decisions made based on them."),
        
        ("4. No Endorsement of Third-Party Tools",
         "The use of third-party tools and data sources in AI evaluations is at the user's discretion. RAA Capital Partners Sdn Bhd, Centre for AI Innovation (CEAI) and its advisory partners do not endorse or guarantee the performance or accuracy of any third-party tools or data sources used in conjunction with the AI-generated reports.")
    ]

    for title, content in disclaimers:
        elements.append(Paragraph(title, disclaimer_styles['item_header']))
        elements.append(Paragraph(content, disclaimer_styles['body_text']))

    # Add bottom line
    elements.append(Table(
        [['']],
        colWidths=[7.5*inch],
        style=TableStyle([
            ('LINEABOVE', (0,0), (-1,0), 1, colors.black),
        ])
    ))

    # Add "strictly confidential"
    elements.append(Paragraph("strictly confidential", disclaimer_styles['confidential']))
def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'#{1,6}\s?', '', text)  # Remove markdown headers
    text = re.sub(r'[\*_`]', '', text)      # Remove markdown formatting
    text = re.sub(r'\.{2,}', '.', text)     # Clean up multiple periods
    return ' '.join(text.split()).strip()
def create_highlight_box(text, styles):
    """Create highlighted box with consistent styling"""
    return Table(
        [[Paragraph(f"• {text}", styles['content'])]],
        colWidths=[6*inch],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')),
            ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#90CDF4')),
            ('PADDING', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ])
    )
def create_second_page(styles, org_info):
    """Create an enhanced front page with modern design elements"""
    elements = []
    
    # Add some space at the top
    elements.append(Spacer(1, 1*inch))
    
    # Create a colored banner for the title
    title_table = Table(
        [[Paragraph("Profile Analysis", styles['title'])]],
        colWidths=[7*inch],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F9FF')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 30),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 30),
            ('LEFTPADDING', (0, 0), (-1, -1), 20),
            ('RIGHTPADDING', (0, 0), (-1, -1), 20),
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2B6CB0')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2B6CB0')),
        ])
    )
    elements.append(title_table)
    
    # Add space before organization info
    elements.append(Spacer(1, 1*inch))
    
    # Create a styled box for organization info
    org_info_content = [
        [Paragraph("Organization Profile", styles['subheading'])],
        [Table(
            [
                [
                    Paragraph("Organization Type", 
                             ParagraphStyle('Label', parent=styles['content'], textColor=colors.HexColor('#2B6CB0'), fontSize=12)),
                    Paragraph(str(org_info.get('type', 'N/A')), styles['content'])
                ],
                [
                    Paragraph("Industry Sector",
                             ParagraphStyle('Label', parent=styles['content'], textColor=colors.HexColor('#2B6CB0'), fontSize=12)),
                    Paragraph(str(org_info.get('sector', 'N/A')), styles['content'])  # Make sure we're using 'sector' here
                ],
                [
                    Paragraph("Report Date",
                             ParagraphStyle('Label', parent=styles['content'], textColor=colors.HexColor('#2B6CB0'), fontSize=12)),
                    Paragraph(str(org_info.get('date', 'N/A')), styles['content'])
                ]
            ],
            colWidths=[2*inch, 4*inch],
            style=TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F7FAFC')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ])
        )]
    ]
    
    info_table = Table(
        org_info_content,
        colWidths=[7*inch],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#90CDF4')),
            ('TOPPADDING', (0, 0), (-1, -1), 20),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 30),
            ('RIGHTPADDING', (0, 0), (-1, -1), 30),
        ])
    )
    elements.append(info_table)
    
    # Add decorative footer
    elements.append(Spacer(1, 1*inch))
    footer_text = ParagraphStyle(
        'Footer',
        parent=styles['content'],
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4A5568'),
        fontSize=9
    )
    elements.append(Paragraph(
        "Prepared by Centre for AI Innovation (CEAI)",
        footer_text
    ))
    elements.append(Paragraph(
        f"Generated on {org_info.get('date', 'N/A')}",
        footer_text
    ))
    
    return elements
def create_custom_styles():
    base_styles = getSampleStyleSheet()
    
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Italic', 'fonts/Lato-Italic.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-BoldItalic', 'fonts/Lato-BoldItalic.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'

    styles = {
        'Normal': base_styles['Normal'],
        'TOCEntry': ParagraphStyle(
            'TOCEntry',
            parent=base_styles['Normal'],
            fontSize=12,
            leading=16,
            leftIndent=20,
            fontName=base_font
        ),
        'title': ParagraphStyle(
            'CustomTitle',
            parent=base_styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#2B6CB0'),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName=bold_font,
            leading=28.8
        ),
        'heading': ParagraphStyle(
            'CustomHeading',
            parent=base_styles['Normal'],
            fontSize=26,
            textColor=colors.HexColor('#1a1a1a'),
            spaceBefore=20,
            spaceAfter=15,
            fontName=bold_font,
            leading=40.5,
            tracking=0
        ),
        'subheading': ParagraphStyle(
            'CustomSubheading',
            parent=base_styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4A5568'),
            spaceBefore=15,
            spaceAfter=10,
            fontName=bold_font,
            leading=18.2
        ),
        'normal': ParagraphStyle(
            'CustomNormal',
            parent=base_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            spaceBefore=6,
            spaceAfter=6,
            fontName=base_font,
            leading=15.4,
            tracking=0
        ),
        'content': ParagraphStyle(
            'CustomContent',
            parent=base_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_JUSTIFY,
            spaceBefore=6,
            spaceAfter=6,
            fontName=base_font,
            leading=15.4,
            tracking=0
        ),
        'bullet': ParagraphStyle(
            'CustomBullet',
            parent=base_styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            leftIndent=20,
            firstLineIndent=0,
            fontName=base_font,
            leading=15.4,
            tracking=0
        )
    }
    
    return styles
def scale_image_to_fit(image_path, max_width, max_height):
    """Scale image to fit within maximum dimensions while maintaining aspect ratio."""
    from PIL import Image as PILImage
    import os
    
    if not os.path.exists(image_path):
        return None
        
    try:
        img = PILImage.open(image_path)
        img_width, img_height = img.size
        
        # Calculate scaling factor
        width_ratio = max_width / img_width
        height_ratio = max_height / img_height
        scale = min(width_ratio, height_ratio)
        
        new_width = img_width * scale
        new_height = img_height * scale
        
        return new_width, new_height
    except Exception as e:
        print(f"Error scaling image: {str(e)}")
        return None

def create_front_page(styles, org_info):
    """Create a front page using a full-page cover image."""
    elements = []
    
    if os.path.exists("frontemma.png"):
        # Create full page image without margins
        img = Image(
            "frontemma.png",
            width=letter[0],     # Full letter width (8.5 inches)
            height=letter[1]     # Full letter height (11 inches)
        )
        elements.append(img)
    else:
        # Fallback content if image is missing
        elements.extend([
            Spacer(1, 2*inch),
            Paragraph("ESG Assessment Report", styles['title']),
            Spacer(1, 1*inch),
            Paragraph(f"Organization: {org_info['organization_name']}", styles['content']),
            Paragraph(f"Date: {org_info['date']}", styles['content'])
        ])
    
    return elements


def process_content(content, styles, elements):
    """Process content with proper formatting"""
    if not content:
        return
    
    paragraphs = content.strip().split('\n')
    for para in paragraphs:
        clean_para = clean_text(para)
        if not clean_para:
            continue
        if "Summary" in clean_para:
            elements.append(Paragraph(clean_para, styles['subheading']))  # Add as a subheading
            continue
        if "Strengths and Advantages" in clean_para:
            elements.append(Paragraph(clean_para, styles['subheading']))  # Add as a subheading
            continue
        if "Skills and Competencies" in clean_para:
            elements.append(Paragraph(clean_para, styles['subheading']))  # Add as a subheading
            continue

        if "Compatible Personality and Behavioral Insights" in clean_para:
            elements.append(PageBreak())  # Add a page break
            elements.append(Paragraph(clean_para, styles['subheading']))  # Add as a subheading
            continue
        
        # Handle numbered points
        point_match = re.match(r'^\d+\.?\s+(.+)', clean_para)
        if point_match:
            elements.extend([
                Spacer(1, 0.1*inch),
                create_highlight_box(point_match.group(1), styles),
                Spacer(1, 0.1*inch)
            ])
        # Handle bullet points
        elif clean_para.startswith(('•', '-', '*')):
            elements.append(
                Paragraph(
                    f"• {clean_para.lstrip('•-* ')}",
                    styles['bullet']
                )
            )
        else:
            elements.append(Paragraph(clean_para, styles['content']))
            elements.append(Spacer(1, 0.05*inch))
def create_header_footer(canvas, doc):
    """Add header and footer with smaller, transparent images in the top right and a line below the header."""
    canvas.saveState()
    
    # Register Lato fonts if available
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    if doc.page > 1:  # Only show on pages after the first page
        # Adjust the position to the top right
        x_start = doc.width + doc.leftMargin - 1.0 * inch  # Align closer to the right
        y_position = doc.height + doc.topMargin - 0.1 * inch  # Slightly below the top margin
        image_width = 0.5 * inch  # Smaller width
        image_height = 0.5 * inch  # Smaller height

        # Draw images (ensure they are saved with transparent backgrounds)
        if os.path.exists("ceai.png"):
            canvas.drawImage(
                "ceai.png", 
                x_start, 
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        if os.path.exists("raa.png"):
            canvas.drawImage(
                "raa.png", 
                x_start - image_width - 0.1 * inch,
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        if os.path.exists("emma.png"):
            canvas.drawImage(
                "emma.png", 
                x_start - 2 * (image_width + 0.1 * inch),
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        # Add Header Text using Lato Bold
        canvas.setFont(bold_font, 24)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.1*inch, 
                         "ESG Starter's Kit")

        # Draw line below the header text
        line_y_position = doc.height + doc.topMargin - 0.30 * inch
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, line_y_position, doc.width + doc.rightMargin, line_y_position)

        # Footer using regular Lato
        canvas.setFont(base_font, 9)
        canvas.drawString(doc.leftMargin, 0.5 * inch, 
                          f"Generated on {datetime.datetime.now().strftime('%B %d, %Y')}")
        canvas.drawRightString(doc.width + doc.rightMargin, 0.5 * inch, 
                               f"Page {doc.page}")
    canvas.restoreState()
def create_header_footer_disclaimer(canvas, doc):
    """Add header and footer with smaller, transparent images in the top right and a line below the header."""
    canvas.saveState()
    
    # Register Lato fonts if available
    try:
        pdfmetrics.registerFont(TTFont('Lato', 'fonts/Lato-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('Lato-Bold', 'fonts/Lato-Bold.ttf'))
        base_font = 'Lato'
        bold_font = 'Lato-Bold'
    except:
        # Fallback to Helvetica if Lato fonts are not available
        base_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
    
    if doc.page > 1:  # Only show on pages after the first page
        # Adjust the position to the top right
        x_start = doc.width + doc.leftMargin - 1.0 * inch  # Align closer to the right
        y_position = doc.height + doc.topMargin - 0.1 * inch  # Slightly below the top margin
        image_width = 0.5 * inch  # Smaller width
        image_height = 0.5 * inch  # Smaller height

        # Draw images (ensure they are saved with transparent backgrounds)
        if os.path.exists("ceai.png"):
            canvas.drawImage(
                "ceai.png", 
                x_start, 
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        if os.path.exists("raa.png"):
            canvas.drawImage(
                "raa.png", 
                x_start - image_width - 0.1 * inch,
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        if os.path.exists("emma.png"):
            canvas.drawImage(
                "emma.png", 
                x_start - 2 * (image_width + 0.1 * inch),
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        # Add Header Text - Fixed by properly setting font name and size
        canvas.setFont(bold_font, 27)  # Set font with name and size
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.1*inch, 
                         "Disclaimer")

        # Draw line below the header text
        line_y_position = doc.height + doc.topMargin - 0.30 * inch
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, line_y_position, doc.width + doc.rightMargin, line_y_position)

        # Footer - Fixed by properly setting font name and size
        canvas.setFont(base_font, 9)  # Set font with name and size
        canvas.drawString(doc.leftMargin, 0.5 * inch, 
                         f"Generated on {datetime.datetime.now().strftime('%B %d, %Y')}")
        canvas.drawRightString(doc.width + doc.rightMargin, 0.5 * inch, 
                             f"Page {doc.page}")
    
    canvas.restoreState()
def get_esg_analysis1(user_data, api_key):
    """Initial ESG analysis based on profile"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on this organization's profile and ESG readiness responses:
    {user_data}
    
    Provide a 535-word analysis with specific references to the data provided, formatted
    in narrative form with headers and paragraphs.NO NUMBERING POINTS"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error getting initial analysis: {str(e)}")
        return None

def get_esg_analysis2(user_data, api_key):
    """Get organization-specific ESG recommendations, supporting multiple organization types."""
    import json
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    user_data_str = json.dumps(user_data, indent=2)

    # ESG frameworks for various organization types
    prompts = {
        "Public Listed Company": [
            "Bursa Malaysia Sustainability Reporting Guide (3rd Edition)",
            "Securities Commission Malaysia (SC): Malaysian Code on Corporate Governance (MCCG)",
            "Global Reporting Initiative (GRI)",
            "Task Force on Climate-related Financial Disclosures (TCFD)",
            "Sustainability Accounting Standards Board (SASB)",
            "GHG Protocol",
            "ISO 14001",
            "ISO 26000",
        ],
        "Financial Institution": [
            "Bank Negara Malaysia (BNM) Climate Change and Principle-based Taxonomy (CCPT)",
            "Malaysian Sustainable Finance Roadmap",
            "Principles for Responsible Banking (PRB)",
            "Task Force on Climate-related Financial Disclosures (TCFD)",
            "Sustainability Accounting Standards Board (SASB)",
            "GHG Protocol",
            "ISO 14097",
        ],
        "SME/Enterprise": [
            "Simplified ESG Disclosure Guide (SEDG)",
            "Bursa Malaysia's Basic Sustainability Guidelines for SMEs",
            "ISO 14001",
            "Global Reporting Initiative (GRI)",
            "GHG Protocol",
            "ISO 26000",
            "Sustainability Accounting Standards Board (SASB)",
        ],
        "Government Agency": [
            "Malaysian Code on Corporate Governance (MCCG)",
            "United Nations Sustainable Development Goals (SDGs)",
            "International Public Sector Accounting Standards (IPSAS)",
            "ISO 26000",
            "GHG Protocol",
        ],
        "NGO": [
            "Global Reporting Initiative (GRI)",
            "Social Value International (SVI)",
            "ISO 26000",
            "United Nations Sustainable Development Goals (SDGs)",
            "GHG Protocol",
        ],
        "Others": [
            "UN Principles for Responsible Management Education (PRME)",
            "ISO 26000",
            "Sustainability Development Goals (SDGs)",
            "GHG Protocol",
            "ISO 14001",
        ],
    }

    # Get organization types from user_data
    org_types = user_data.get("organization_types", [])
    if not org_types:
        org_types = ["Others"]  # Default to Others if no type is specified
    
    # Create a section for each selected organization type
    org_type_sections = []
    all_frameworks = set()  # To track unique frameworks across all types
    
    for org_type in org_types:
        frameworks = prompts.get(org_type, prompts["Others"])
        all_frameworks.update(frameworks)
        org_type_sections.append(f"""
Organization Type: {org_type}
Relevant Frameworks:
{chr(10).join('- ' + framework for framework in frameworks)}
""")

    # Create the full prompt with sections for each organization type
    full_prompt = f"""
As an ESG consultant specializing in Malaysian standards and frameworks, provide a comprehensive analysis for an organization with multiple classifications:

Organization Profile:
{user_data_str}

This organization operates under multiple classifications:
{chr(10).join(org_type_sections)}

Please provide:
1. A detailed analysis of how each framework applies to this specific organization
2. Areas of overlap between different frameworks that create synergies
3. Potential conflicts or challenges in implementing multiple framework requirements
4. Recommendations for prioritizing and harmonizing framework implementation
5. Specific examples of how the organization can benefit from its multi-framework approach

Write in narrative form (450 words) with headers and Numbering points(no bullet points), including:
- Supporting facts and figures
- Specific references for each organization type
- Cross-framework integration strategies
- Implementation recommendations

Focus on practical implementation while acknowledging the complexity of managing multiple frameworks."""

    # Process the prompt with OpenAI's API
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error getting ESG analysis: {str(e)}"
def generate_management_questions(analysis1, analysis2, api_key):
    """Generate top 10 management issues/questions"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on the previous analyses:
    {analysis1}
    {analysis2}
    
    Generate a list of top 10 issues/questions that Management should address in numbering Points.
    Format as  650-words in narrative form with:
    - Clear headers for key areas
    - Bullet points identifying specific issues
    - Supporting facts and figures
    - Industry-specific references"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # Increased token limit
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating management questions: {str(e)}")
        return None

def generate_question_rationale(questions, analysis1, analysis2, api_key):
    """Generate rationale for management questions"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on these management issues and previous analyses:
    {questions}
    {analysis1}
    {analysis2}
    
    Provide a 680-word (no numbering points)explanation of why each issue needs to be addressed, with:
    - Specific references to ESG guidelines and standards
    - Industry best practices
    - Supporting facts and figures
    - Framework citations"""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating management questions: {str(e)}")
        return None

def generate_implementation_challenges(analysis1, analysis2, questions, api_key):
    """Generate implementation challenges analysis"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on the previous analyses:
    {analysis1}
    {analysis2}
    {questions}
    
    Provide a 680-word(no numbering points) analysis of potential ESG implementation challenges covering:
    1. Human Capital Availability and Expertise
    2. Budgeting and Financial Resources
    3. Infrastructure
    4. Stakeholder Management
    5. Regulatory Compliance
    6. Other Challenges
    
    Format in narrative form with supporting facts and specific references."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating challenges analysis: {str(e)}")
        return None
def generate_advisory_analysis(user_data, all_analyses, api_key):
    """Generate advisory plan and SROI model"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on all previous analyses:
    {user_data}
    {all_analyses}
    
     (480 words): Explain what and how ESG Advisory team can assist in numbering points, including:
    - Implementation support methods
    - Technical expertise areas
    - Training programs
    - Monitoring systems
    
    Include supporting facts, figures, and statistical references."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating advisory and SROI analysis: {str(e)}")
        return None
def generate_sroi_analysis(user_data, all_analyses, api_key):
    """Generate advisory plan and SROI model"""
    client = OpenAI(api_key=api_key)
    
    prompt = f"""Based on all previous analyses:
    {user_data}
    {all_analyses}
    
    (730 words): Provide a Social Return on Investment (SROI) model with(in numbering points):
    1. Calculation Methodology:
    - Explain SROI calculations using plain text (avoid mathematical notation)
    - Example: "For every 1 dollar invested, X value is generated" instead of mathematical formulas
    - Use clear, narrative descriptions of calculations
    
    2. Financial Projections:
    - Present numbers in plain text format
    - Use clear currency formatting (e.g., "RM 1,000" instead of mathematical notation)
    - Write ratios in plain language
    
    3. Implementation Guidelines:
    - Use clear, narrative text
    - Avoid special characters or mathematical symbols
    - Present steps in numbered format
    
    Format all numerical examples in plain text with proper spacing."""

    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating advisory and SROI analysis: {str(e)}")
        return None
def render_header():
    """Render application header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        logo_path = "emma.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=150)
    with col2:
        logo_path = "finb.jpg"
        if os.path.exists(logo_path):
            st.image(logo_path, width=250)
def main():
    st.set_page_config(page_title="ESG Starter's Kit", layout="wide")
    
    st.title("ESG Starter's Kit")
    render_header()
    # API Key input in sidebar
    with st.sidebar:
        api_key = st.text_input("OpenAI API Key", type="password")
        if not api_key:
            st.warning("Please enter your OpenAI API key to continue.")
            return

    # Initialize session state
    if 'session' not in st.session_state:
        st.session_state.session = 1

    # Session 1: Initial Assessment
    st.header("1️⃣ Organization Profile & ESG Readiness")
    with st.form("session1_form"):
        org_name = st.text_input("Organization Name")
        industry = st.selectbox("Industry", FIELDS_OF_INDUSTRY)
        if industry == "Others":
            industry = st.text_input("Please specify your industry")
        
        core_activities = st.text_area("Describe your organization's core activities")
        
        st.subheader("ESG Readiness Assessment")
        esg_responses = {}
        for question, options in ESG_READINESS_QUESTIONS.items():
            response = st.radio(question, options, index=None)
            if response:
                esg_responses[question] = response
        
        submit_session1 = st.form_submit_button("Submit and Generate Initial Analysis")
        
        if submit_session1:
            if not all([org_name, industry, core_activities]):
                st.error("Please fill in all fields.")
            elif len(esg_responses) != len(ESG_READINESS_QUESTIONS):
                st.error("Please answer all ESG readiness questions.")
            else:
                st.session_state.user_data = {
                    "organization_name": org_name,
                    "industry": industry,
                    "core_activities": core_activities,
                    "esg_responses": esg_responses
                }
                
                with st.spinner("Generating initial analysis..."):
                    st.session_state.analysis1 = get_esg_analysis1(
                        st.session_state.user_data, 
                        api_key
                    )
                    if st.session_state.analysis1:
                        st.session_state.session = 2

    # Display Analysis 1 and Session 2
    if hasattr(st.session_state, 'analysis1'):
        st.markdown(st.session_state.analysis1)
    
    if st.session_state.session >= 2:
        st.header("2️⃣ Framework Selection")
        selected_types = []
        
        # Create checkboxes for each organization type
        for org_type in ORGANIZATION_TYPES:
            if st.checkbox(org_type, key=f"org_type_{org_type}"):
                selected_types.append(org_type)
                # Special handling for "Others"
                if org_type == "Others":
                    other_framework = st.text_area(
                        "Specify your frameworks (one per line)",
                        key="other_frameworks"
                    )

        # Generate Framework Analysis button
        if st.button("Generate Framework Analysis"):
            if not selected_types:
                st.error("Please select at least one organization type.")
            else:
                st.session_state.user_data["organization_types"] = selected_types
                # If "Others" is selected, add the custom frameworks
                if "Others" in selected_types and "other_frameworks" in st.session_state:
                    other_frameworks = st.session_state.other_frameworks.split('\n')
                    # Only include non-empty lines
                    other_frameworks = [f for f in other_frameworks if f.strip()]
                    st.session_state.user_data["other_frameworks"] = other_frameworks
                
                with st.spinner("Generating framework analysis..."):
                    st.session_state.analysis2 = get_esg_analysis2(
                        st.session_state.user_data,
                        api_key
                    )
                    if st.session_state.analysis2:
                        st.session_state.session = 3

    # Display Analysis 2 and Generate Management Questions
    if hasattr(st.session_state, 'analysis2'):
        st.markdown(st.session_state.analysis2)
        
        if st.session_state.session >= 3:
            st.header("3️⃣ Management Issues")
            
            if 'management_questions' not in st.session_state:
                with st.spinner("Generating management issues..."):
                    st.session_state.management_questions = generate_management_questions(
                        st.session_state.analysis1,
                        st.session_state.analysis2,
                        api_key
                    )
            
            if hasattr(st.session_state, 'management_questions'):
                st.markdown(st.session_state.management_questions)
                
                # Session 4: Question Rationale
                st.header("4️⃣ Issue Rationale")
                
                if 'question_rationale' not in st.session_state:
                    with st.spinner("Generating rationale..."):
                        st.session_state.question_rationale = generate_question_rationale(
                            st.session_state.management_questions,
                            st.session_state.analysis1,
                            st.session_state.analysis2,
                            api_key
                        )
                
                if hasattr(st.session_state, 'question_rationale'):
                    st.markdown(st.session_state.question_rationale)
                    
                    # Session 5: Implementation Challenges
                    st.header("5️⃣ Implementation Challenges")
                    
                    if 'implementation_challenges' not in st.session_state:
                        with st.spinner("Analyzing implementation challenges..."):
                            st.session_state.implementation_challenges = generate_implementation_challenges(
                                st.session_state.analysis1,
                                st.session_state.analysis2,
                                st.session_state.management_questions,
                                api_key
                            )
                    
                    if hasattr(st.session_state, 'implementation_challenges'):
                        st.markdown(st.session_state.implementation_challenges)
                        
                        # Session 6: Advisory Plan & SROI Model
                        st.header("6️⃣ Advisory Plan")
                        
                        if 'advisory' not in st.session_state:
                            all_analyses = {
                                'analysis1': st.session_state.analysis1,
                                'analysis2': st.session_state.analysis2,
                                'management_questions': st.session_state.management_questions,
                                'question_rationale': st.session_state.question_rationale,
                                'implementation_challenges': st.session_state.implementation_challenges
                            }
                            
                            with st.spinner("Generating advisory plan..."):
                                st.session_state.advisory = generate_advisory_analysis(
                                    st.session_state.user_data,
                                    all_analyses,
                                    api_key
                                )
                        
                        if hasattr(st.session_state, 'advisory'):
                            st.markdown(st.session_state.advisory)
                        
                        # Session 7: SROI Model
                        st.header("7️⃣ SROI Model")
                        
                        if 'sroi' not in st.session_state:
                            all_analyses = {
                                'analysis1': st.session_state.analysis1,
                                'analysis2': st.session_state.analysis2,
                                'management_questions': st.session_state.management_questions,
                                'question_rationale': st.session_state.question_rationale,
                                'implementation_challenges': st.session_state.implementation_challenges,
                                'advisory': st.session_state.advisory
                            }
                            
                            with st.spinner("Generating SROI model..."):
                                st.session_state.sroi = generate_sroi_analysis(
                                    st.session_state.user_data,
                                    all_analyses,
                                    api_key
                                )
                        
                        if hasattr(st.session_state, 'sroi'):
                            st.markdown(st.session_state.sroi)
                            
                            # Generate PDF only when all analyses are complete
                            if (hasattr(st.session_state, 'analysis1') and 
                                hasattr(st.session_state, 'analysis2') and 
                                hasattr(st.session_state, 'management_questions') and 
                                hasattr(st.session_state, 'implementation_challenges') and 
                                hasattr(st.session_state, 'advisory') and 
                                hasattr(st.session_state, 'sroi')):
                                try:
                                    esg_data = {
                                        'analysis1': st.session_state.analysis1,
                                        'analysis2': st.session_state.analysis2,
                                        'management_questions': st.session_state.management_questions,
                                        'implementation_challenges': st.session_state.implementation_challenges,
                                        'advisory': st.session_state.advisory,
                                        'sroi': st.session_state.sroi
                                    }
                                    
                                    personal_info = {
                                        'organization_name': st.session_state.user_data['organization_name'],
                                        'sector': st.session_state.user_data['industry'],  # Changed from 'industry' to 'sector' to match PDF template
                                        'type': ', '.join(st.session_state.user_data['organization_types']),
                                        'date': datetime.datetime.now().strftime('%B %d, %Y')
                                    }
                                    page_numbers = [4, 6, 8, 11, 13, 15] 
                                    pdf_buffer = generate_pdf(esg_data, personal_info,page_numbers)
                                    
                                    # Download button
                                    st.download_button(
                                        "📥 Download ESG Assessment Report",
                                        data=pdf_buffer,
                                        file_name=f"esg_assessment_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                                        mime="application/pdf",
                                        help="Click to download your ESG assessment report"
                                    )
                                except Exception as e:
                                    st.error(f"Error generating PDF: {str(e)}")
                                    print(f"Detailed error: {str(e)}")
if __name__ == "__main__":
    main()
