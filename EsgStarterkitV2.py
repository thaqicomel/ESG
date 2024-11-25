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
def generate_pdf(esg_data, personal_info):
    """Generate PDF with ESG analysis data"""
    buffer = io.BytesIO()
    
    # Create document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=1.5*inch,
        bottomMargin=inch
    )
    
    # Create frames
    full_page_frame = Frame(
        0,              # x = 0
        0,              # y = 0
        letter[0],      # width = full page width
        letter[1],      # height = full page height
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0
    )
    
    normal_frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id='normal'
    )
    
    # Create page templates
    templates = [
        PageTemplate(
            id='First',
            frames=[full_page_frame],
            onPage=lambda canvas, doc: None  # No header/footer on first page
        ),
        PageTemplate(
            id='Later',
            frames=[normal_frame],
            onPage=create_header_footer
        )
    ]
    doc.addPageTemplates(templates)
    
    styles = create_custom_styles()
    elements = []
    
    # Cover page setup
    elements.append(NextPageTemplate('First'))
    
    # Cover page with full-page image
    if os.path.exists("frontemma.png"):
        img = Image(
            "frontemma.png",
            width=letter[0],
            height=letter[1]
        )
        elements.append(img)
    
    # Important: Set the Later template before the page break
    elements.append(NextPageTemplate('Later'))
    elements.append(PageBreak())
    
    # Initial ESG Assessment - now will use Later template
    elements.append(Paragraph("ESG Initial Assessment", styles['heading']))
    process_content(esg_data['analysis1'], styles, elements)
    elements.append(PageBreak())
    
    # Rest of the content (no need to keep setting Later template)
    elements.append(Paragraph("Framework Analysis", styles['heading']))
    process_content(esg_data['analysis2'], styles, elements)
    elements.append(PageBreak())
    
    elements.append(Paragraph("Management Issues", styles['heading']))
    process_content(esg_data['management_questions'], styles, elements)
    elements.append(PageBreak())
    
    elements.append(Paragraph("Implementation Challenges", styles['heading']))
    process_content(esg_data['implementation_challenges'], styles, elements)
    elements.append(PageBreak())
    
    elements.append(Paragraph("Advisory Plan", styles['heading']))
    process_content(esg_data['advisory'], styles, elements)
    elements.append(PageBreak())

    elements.append(Paragraph("SROI Analysis", styles['heading']))
    process_content(esg_data['sroi'], styles, elements)
    elements.append(PageBreak())
    
    # Contact page
    elements.extend(create_contact_page(styles))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
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
def create_custom_styles():
    """Create custom styles for the PDF with proper style inheritance"""
    styles = getSampleStyleSheet()
    
    # Custom paragraph styles
    return {
        'title': ParagraphStyle(
            'CustomTitle',
            parent=styles['Normal'],
            fontSize=24,
            textColor=colors.HexColor('#2B6CB0'),
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica-Bold'
        ),
        'heading': ParagraphStyle(
            'CustomHeading',
            parent=styles['Normal'],
            fontSize=20,
            textColor=colors.HexColor('#1a1a1a'),
            spaceBefore=20,
            spaceAfter=15,
            fontName='Helvetica-Bold'
        ),
        'subheading': ParagraphStyle(
            'CustomSubheading',
            parent=styles['Normal'],
            fontSize=13,
            textColor=colors.HexColor('#4A5568'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ),
        'content': ParagraphStyle(
            'CustomContent',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_JUSTIFY,
            spaceBefore=6,
            spaceAfter=6,
            fontName='Helvetica'
        ),
        'bullet': ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            leftIndent=20,
            firstLineIndent=0,
            fontName='Helvetica'
        )
    }

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
def create_contact_page(styles):
    """Create a beautifully designed contact page with fixed sizing."""
    elements = []
    
    # Add a page break before contact page
    # elements.append(PageBreak())
    
    # Create a colored background header
    elements.append(
        Table(
            [[Paragraph("Get in Touch", styles['heading'])]], 
            colWidths=[7*inch],
            style=TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F9FF')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 20),
                ('TOPPADDING', (0, 0), (-1, -1), 20),
                ('LEFTPADDING', (0, 0), (-1, -1), 30),
            ])
        )
    )
    elements.append(Spacer(1, 0.3*inch))

    # Profile photo
    if os.path.exists("mizah.jpg"):
        description_style = ParagraphStyle(
            'ImageDescription',
            parent=styles['content'],
            fontSize=10,
            textColor=colors.HexColor('#1a1a1a'),
            alignment=TA_LEFT,
            leading=14
        )
        
        description_text = Paragraph("""KerjayaKu: AI-Driven Career Guidance for a Strategic Future<br/>
            KerjayaKu is an AI-powered portal designed to help fresh graduates and young professionals strategically navigate their career development journey. 
            By integrating cutting-edge artificial intelligence, KerjayaKu assesses your education profile, aspirations, personality traits, current skillset, 
            and problem-solving abilities, along with social-emotional learning skills. It then delivers personalized insights to help you stay competitive 
            in today's dynamic job market.""", description_style)

        elements.append(
            Table(
                [
                    [Image("mizah.jpg", width=1*inch, height=1*inch), ""],  # Image row
                    [description_text, ""]  # Description row below image
                ],
                colWidths=[1.5*inch, 5.5*inch],
                style=TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'LEFT'),  # Align image to left
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                    ('LEFTPADDING', (0, 0), (-1, -1), 15),
                    ('SPAN', (0, 1), (1, 1)),  # Span description across both columns
                ])
            )
        )
        elements.append(Spacer(1, 0.3*inch))

    # Contact information table
    contact_table_data = [
        # Label Cell, Value Cell
        [Paragraph("Address:", styles['content']),
         Paragraph("Centre for AI Innovation (CEAI) @Kuala Lumpur,\nc/o MyFinB (M) Sdn Bhd,\nLevel 13A, Menara Tokio Marine,\n189 Jalan Tun Razak, Hampshire Park,\n50450 Kuala Lumpur, Malaysia", styles['content'])],
        
        [Paragraph("Tel:", styles['content']),
         Paragraph("+601117695760", styles['content'])],
        
        [Paragraph("Email:", styles['content']),
         Paragraph('<link href="mailto:hamizah@ceaiglobal.com"><font color="#2563EB">hamizah@ceaiglobal.com</font></link>', styles['content'])],
        
        [Paragraph("Website:", styles['content']),
         Paragraph('<link href="https://www.google.com/maps"><font color="#2563EB">www.ceaiglobal.com</font></link>', styles['content'])]
    ]

    # Create the contact information table
    contact_table = Table(
        contact_table_data,
        colWidths=[1.5*inch, 5.8*inch],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFFFFF')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2B6CB0')),  # Blue color for labels
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
        ])
    )
    
    elements.append(contact_table)
    
    # Footer
    elements.extend([
        Spacer(1, 0.5*inch),
        Table(
            [[Paragraph("Thank you for your interest!", 
                       ParagraphStyle(
                           'ThankYou',
                           parent=styles['subheading'],
                           alignment=TA_CENTER,
                           textColor=colors.HexColor('#2B6CB0')
                       ))]],
            colWidths=[7*inch],
            style=TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F0F9FF')),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 15),
            ])
        ),
        # Spacer(1, 0.2*inch),
        # Table(
        #     [[Paragraph("© 2024 Centre for AI Innovation. All rights reserved.", 
        #                ParagraphStyle(
        #                    'Footer',
        #                    parent=styles['content'],
        #                    alignment=TA_CENTER,
        #                    textColor=colors.HexColor('#666666'),
        #                    fontSize=8
        #                ))]],
        #     colWidths=[7*inch],
        #     style=TableStyle([
        #         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        #     ])
        # )
    ])
    
    return elements
def create_header_footer(canvas, doc):
    """Add header and footer with smaller, transparent images in the top right and a line below the header."""
    canvas.saveState()
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
                mask="auto"  # Enable transparency for PNGs
            )
        
        if os.path.exists("raa.png"):
            canvas.drawImage(
                "raa.png", 
                x_start - image_width - 0.1 * inch,  # Adjust for stacking to the left
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        if os.path.exists("emma.png"):
            canvas.drawImage(
                "emma.png", 
                x_start - 2 * (image_width + 0.1 * inch),  # Adjust for stacking to the left
                y_position, 
                width=image_width, 
                height=image_height, 
                mask="auto"
            )
        
        # Add Header Text
        canvas.setFont('Helvetica-Bold', 10)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 0.1*inch, 
                         "ESG Starter's Kit")

        # Draw line below the header text
        line_y_position = doc.height + doc.topMargin - 0.30 * inch
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, line_y_position, doc.width + doc.rightMargin, line_y_position)

        # Footer
        canvas.setFont('Helvetica', 9)
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
    
    Provide a 730-word analysis with specific references to the data provided, formatted
    in narrative form with headers and paragraphs."""

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

Write in narrative form (680 words) with headers and bullet points, including:
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
    
    Generate a list of top 10 issues/questions that Management should address.
    Format as  700-words in narrative form with:
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
    
    Provide a 750-word explanation of why each issue needs to be addressed, with:
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
    
    Provide a 700-word analysis of potential ESG implementation challenges covering:
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
    
     (700 words): Explain what and how ESG Advisory team can assist, including:
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
    
    (700 words): Provide a Social Return on Investment (SROI) model with:
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
                                    
                                    pdf_buffer = generate_pdf(esg_data, personal_info)
                                    
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