from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, PageBreak, Image as Img, Table, TableStyle,Flowable,KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Line
from pyairtable import Api,Table as airtable_obj

from reportlab.lib.pagesizes import letter 
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER

import os
import requests
import ast
import openai
import json

from PyPDF2 import PdfReader, PdfWriter
# from lead_magnet.industry_insights import get_cold_email_kpis
from lead_magnet.client_info_parser import collect_information
from lead_magnet.competitor_insights import get_competitors_list
from lead_magnet.personalized_planner import generate_personalized_planner
# from error_logger import execute_error_block
from lead_magnet.email_module import send_lead_magnet_email

from reportlab.lib.enums import TA_CENTER

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_CLIENT_TABLE_NAME = os.getenv("AIRTABLE_CLIENT_TABLE_NAME")
CLIENT_INFO_TABLE_NAME = os.getenv("CLIENT_INFO_TABLE_NAME")
CLIENT_NAME = 'cl_taippa_marketing'
print(f"Client info table for Lead Magnet : {CLIENT_INFO_TABLE_NAME}")


# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Path to fonts directory
FONTS_DIR = os.path.join(SCRIPT_DIR, 'fonts')
PICKLE_DIR = os.path.join(SCRIPT_DIR, 'files')

pdfmetrics.registerFont(TTFont('Anton', os.path.join(FONTS_DIR, 'Anton-Regular.ttf')))
pdfmetrics.registerFont(TTFont('Poppins', os.path.join(FONTS_DIR, 'Poppins-Regular.ttf')))
pdfmetrics.registerFont(TTFont('PoppinsBold', os.path.join(FONTS_DIR, 'Poppins-Bold.ttf')))
pdfmetrics.registerFont(TTFont('Switzer', os.path.join(FONTS_DIR, 'Switzer-Light.ttf')))

from reportlab.platypus import Flowable
from reportlab.lib import colors
from reportlab.lib.utils import simpleSplit

import os
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


AIRTABLE_TABLE_NAME = "outreach_guideline"

# Google Drive scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def upload_to_drive(file_path):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype='application/pdf')

    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = uploaded_file.get('id')

    service.permissions().create(
        fileId=file_id,
        body={'role': 'reader', 'type': 'anyone'},
    ).execute()

    return f"https://drive.google.com/uc?id={file_id}&export=download"

def find_airtable_record_by_linkedin(linkedin_url):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {"Authorization": f"Bearer {AIRTABLE_API_KEY}"}
    params = {"filterByFormula": f"{{linkedin_url}}='{linkedin_url}'"}

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    records = data.get('records', [])
    return records[0]['id'] if records else None

def update_airtable_pdf(record_id, file_url):
    url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}/{record_id}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "fields": {
            "lead_magnet_pdf": [{"url": file_url}]
        }
    }
    return requests.patch(url, headers=headers, json=data).json()

class CheckboxItem(Flowable):
    """
    Custom Flowable to create a checkbox with text and appropriate spacing.
    """
    def __init__(self, text, checkbox_size=10, space_between=5, line_spacing=16, margin_left=50, margin_right=50):
        super().__init__()
        self.text = text
        self.checkbox_size = checkbox_size
        self.space_between = space_between
        self.line_spacing = line_spacing  # Space between lines, including for individual checkboxes
        self.margin_left = margin_left  # Margin on the left side of the page
        self.margin_right = margin_right  # Margin on the right side of the page

    def draw(self):
        # Set the stroke and fill colors for the checkbox
        self.canv.setStrokeColor(colors.black)
        self.canv.setFillColor(colors.white)

        # Draw the checkbox
        self.canv.rect(0, -self.checkbox_size, self.checkbox_size, self.checkbox_size, stroke=1, fill=1)

        # Set the font for the text
        self.canv.setFont("Poppins", 10)

        # Calculate the available width for the text, considering margins
        page_width = self.canv._pagesize[0]
        max_width = page_width - self.margin_left - self.margin_right - (self.checkbox_size + self.space_between)

        # Wrap the text if it exceeds the maximum width
        wrapped_lines = simpleSplit(self.text, self.canv._fontname, self.canv._fontsize, max_width)

        # Draw the wrapped lines of text
        for i, line in enumerate(wrapped_lines):
            y_offset = -self.checkbox_size + 2 - (i * self.line_spacing)
            self.canv.drawString(self.checkbox_size + self.space_between, y_offset, line)

    def wrap(self, availWidth, availHeight):
        """
        Calculates the width and height of the flowable based on the text's wrapping.
        """
        # Calculate the available width for wrapping, considering margins
        max_width = availWidth - self.margin_left - self.margin_right - (self.checkbox_size + self.space_between)

        # Determine the number of wrapped lines
        wrapped_lines = simpleSplit(self.text, "Poppins", 10, max_width)

        # Calculate total height: checkbox height + line spacing for additional lines
        total_height = self.checkbox_size + (len(wrapped_lines) - 1) * self.line_spacing + self.line_spacing  # Add extra spacing for separation

        # Return the required width and height
        return availWidth, total_height

def ice_breaker_generator_v2(company_short_description): 
    try:
        prompt = f"""
        Generate a concise and engaging icebreaker based on the following company description.  
        The icebreaker should:
        - Acknowledge the company's industry, expertise, or key achievements if available.  
        - Be warm, natural, and professional.  
        - Show that we understand the company and its value.  
        - Be brief (1-2 sentences) and relevant for initiating a conversation.  
        - Do not ask any questions.  
        - Do not enclose the output in quotes.  

        Company description: {company_short_description}

        This icebreaker will be used in a lead magnet PDF to demonstrate our understanding of the company and create an engaging introduction. Please ensure it is crafted accordingly.
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                    {
                    "role": "system",
                    "content": "You are an expert in creating compelling introductions for lead magnets. Generate a short, engaging, and well-crafted icebreaker suitable for a lead magnet PDF. The output should be text-only, without any additional formatting, disclaimers, or explanations."
                    },
                    {"role": "user", "content": prompt}
                    ],
        )

        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error occured while generating the ice breaker: {e}")

def ice_breaker_generator(company_short_description): 
    try:
        prompt = f"""
        Generate a concise and engaging icebreaker based on the following company description. 
        The icebreaker should:
        - Acknowledge the company's industry, expertise, or key achievements if available.  
        - Be warm, natural, and professional.  
        - Show that we understand the company and its value.  
        - Be brief (1-2 sentences) which can be used as an icebreaker for the first page of a lead magnet personalized PDF that would be sent to the client.  
        - Don't ask any questions.

        Company description: "{company_short_description}"

        This icebreaker will be sent to the client to demonstrate that we have knowledge about their company. 
        Please ensure it is crafted accordingly.

        The output should be text-only, without any additional formatting, disclaimers, or explanations. 
        The output should not exceed 300 characters strictly.
        """

        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert ice breaker creator. Generate a short, engaging, and well-crafted icebreaker. "
                        "The output should be text-only without quotes and shouldn't exceed 300 characters strictly, "
                        "without any additional formatting, disclaimers, or explanations."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"Error occured while generating the ice breaker content: {e}")


# Getting dynamic images from client_details table specific to each client
def get_dynamic_images(table,record_id,attachment_column):
    record = table.get(record_id)
    attachments = record['fields'].get(attachment_column)
    file_names=[]
    print("Getting dynamic images")
    if attachments:
        for attachment in attachments:
            image_url = attachment['url']
            file_name = os.path.join(SCRIPT_DIR,"images/"+attachment['filename'])
            print("\n================")
            print(f"File name: {file_name}")
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(file_name, "wb") as file:
                    file.write(response.content)
                print(f"Downloaded: {file_name}")
                file_names.append(file_name)
            else:
                print(f"Failed to download: {image_url}")
    else:
        print(f"No attachments found in column '{attachment_column}' for record ID '{record_id}'.")
    return file_names


def content_formatting_list(content, is_metrics=False):
    if is_metrics:
        # Parse metrics data which comes in format:
        # 1. **Open Rate:** 25.24%
        # 2. **Click-Through Rate (CTR):** 2-5%
        # 3. **Reply Rate:** 8.5%

        metrics_lines = content.strip().split('\n')
        metrics_data = []

        descriptions = {
            "Open Rate": "The percentage of recipients who open your email",
            "Click-Through Rate (CTR)": "The percentage of recipients who click on links in your email",
            "Reply Rate": "The percentage of recipients who reply to your email"
        }

        for line in metrics_lines:
            # Extract the metric name and value
            parts = line.split(':**')
            if len(parts) == 2:
                # Clean up the metric name
                metric_name = parts[0].replace('1.', '').replace('2.', '').replace('3.', '').replace('**', '').strip()
                # Clean up the value
                value = parts[1].strip()

                # Calculate Taippa target (higher percentages)
                try:
                    if metric_name == "Open Rate":
                        raw_value = float(value.replace('%', ''))
                        taippa_target = f"{raw_value * 1.1:.2f}%"  # 10% higher
                    elif metric_name == "Click-Through Rate (CTR)":
                        if '-' in value:
                            high_end = float(value.split('-')[1].replace('%', ''))
                            taippa_target = f"{high_end * 1.3:.1f}%"  # 30% higher than high end
                        else:
                            raw_value = float(value.replace('%', ''))
                            taippa_target = f"{raw_value * 1.3:.1f}%"  # 30% higher
                    else:  # Reply Rate
                        raw_value = float(value.replace('%', ''))
                        taippa_target = f"{raw_value * 1.5:.1f}%"  # 50% higher
                except ValueError:
                    print(f"Error processing value: {value} for {metric_name}")
                    taippa_target = "N/A"

                metrics_data.append({
                    "header": metric_name,
                    "description": descriptions.get(metric_name, ""),
                    "industry_average": value,
                    "taippa_target": taippa_target
                })

        return json.dumps(metrics_data)
    else:
        prompt = f"""Format the following content into ONLY a JSON array. Do not include any other text:
        [
            {{
                "header": "Emerging Trends in Email Marketing",
                "body": ""
            }},
            {{
                "header": "1. Personalization is Driving Higher Engagement",
                "body": "Emails with personalized subject lines are 26% more likely to be opened. Using AI tools we allow SMEs to personalize content dynamically, leveraging customer behavior and preferences."
            }}
        ]

        Content: {content}"""
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a JSON formatter. Only output the exact JSON array requested, with no additional text, explanations, or formatting."
                },
                {"role": "user", "content": prompt}
            ]
        )

        result = response['choices'][0]['message']['content'].strip()

        try:
            # First try to parse as is
            json.loads(result)
            return result
        except:
            # If that fails, try to clean it up
            try:
                start = result.find('[')
                end = result.rfind(']') + 1
                if start != -1 and end != 0:
                    cleaned = result[start:end]
                    json.loads(cleaned)
                    return cleaned
                else:
                    raise ValueError("Could not find valid JSON array in response")
            except Exception as e:
                print(f"Error parsing response: {result}")
                raise e

def embed_existing_pdf(new_pdf, existing_pdf, last_pager,output_pdf):
    writer = PdfWriter()

    # Add pages from the existing PDF
    # with open(existing_pdf, "rb") as existing_pdf_file:
    #     existing_pdf_reader = PdfReader(existing_pdf_file)
    #     writer.add_page(existing_pdf_reader.pages[0])

    print("Completed first page")
    # Add the new PDF content
    with open(new_pdf, "rb") as new_pdf_file:
        new_pdf_reader = PdfReader(new_pdf_file)
        for page in new_pdf_reader.pages:
            writer.add_page(page)

    # with open(last_pager, "rb") as new_pdf_file:
    #     last_pdf_reader = PdfReader(new_pdf_file)
    #     for page in last_pdf_reader.pages:
    #         writer.add_page(page)

    # Write the final PDF to disk
    with open(output_pdf, "wb") as output_file:
        writer.write(output_file)

def content_formatting_json(content):
    prompt = f"""
    Please convert the content to be only purely JSON text without formatting and without writing json before the actual json code.

    Content: {content}"""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                {
                "role": "system",
                "content": "You are a JSON text formatter. Only output the exact JSON text requested, with no additional text, explanations, or formatting."
                },
                {"role": "user", "content": prompt}
                ],
    )

    result = response.choices[0].message.content
    print(type(result))
    return result


def create_personalized_pdf(user_details, output_path):

    styles = getSampleStyleSheet()

    # Style definitions with reduced spacing
    main_title = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontName="Anton",
        fontSize=24,
        # textColor=colors.HexColor("#c969f5"),
        textColor=colors.purple,
        alignment=1,
        spaceAfter=20,  # Reduced from 30
        borderPadding=15,  # Reduced from 20
        borderWidth=2,
        borderColor=colors.HexColor("#8A2BE2"),
        borderRadius=8
    )

    # Style definitions with reduced spacing
    planner_title_style= ParagraphStyle(
        "GreetingStyle",
        parent=styles["Normal"],
        fontName="PoppinsBold",
        fontSize=16,
        # textColor=colors.HexColor("#f6f2f7"),
        textColor=colors.HexColor("#c969f5"),
        # textColor=colors.pink,
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=18  # Reduced from 20
    )

    greeting_style = ParagraphStyle(
        "GreetingStyle",
        parent=styles["Normal"],
        fontName="PoppinsBold",
        fontSize=16,
        textColor=colors.HexColor("#6292cc"),
        # textColor=colors.HexColor("#c969f5"),
        # textColor=colors.black,
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=18  # Reduced from 20
    )

    # Style definitions with reduced spacing
    planner_title_style_2 = ParagraphStyle(
        "GreetingStyle",
        parent=styles["Normal"],
        fontName="PoppinsBold",
        fontSize=16,
        textColor=colors.HexColor("#6292cc"),
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=18,  # Reduced from 20
        alignment=TA_CENTER
    )

    greeting_style_2 = ParagraphStyle(
        "GreetingStyle",
        parent=styles["Normal"],
        fontName="PoppinsBold",
        fontSize=20,
        textColor=colors.HexColor("#c969f5"),
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=18,  # Reduced from 20
        alignment=TA_CENTER
    )

    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontName="PoppinsBold",
        fontSize=18,
        textColor=colors.HexColor("#6292cc"),
        # textColor=colors.lightblue,
        spaceBefore=15,  # Reduced from 20
        spaceAfter=8,  # Reduced from 10
        leading=22  # Reduced from 24
    )

    ice_breaker_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=13,  # Reduced from 12
        # textColor=colors.HexColor("#f6f2f7"),
        textColor=colors.HexColor("#f5f0f5"),
        # textColor=colors.black,
        leading=14,  # Reduced from 16
        spaceAfter=6,  # Reduced from 8
        leftIndent=20,
        firstLineIndent=-10
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=11,  # Reduced from 12
        # textColor=colors.HexColor("#f6f2f7"),
        textColor=colors.navy,
        leading=14,  # Reduced from 16
        spaceAfter=6,  # Reduced from 8
        leftIndent=20,
        firstLineIndent=-10
    )

    competitor_style = ParagraphStyle(
        "CompetitorStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=10,  # Reduced from 11
        # textColor=colors.HexColor("#f6f2f7"),
        textColor=colors.firebrick,
        leading=12,  # Reduced from 14
        spaceAfter=4,  # Reduced from 6
        leftIndent=25,
        firstLineIndent=0
    )

    metrics_header_style = ParagraphStyle(
        "MetricsHeaderStyle",
        parent=styles["Heading2"],
        fontName="Anton",
        fontSize=14,  # Reduced from 16
        # textColor=colors.HexColor("#6292cc"),
        textColor=colors.red,
        spaceBefore=12,  # Reduced from 15
        spaceAfter=3  # Reduced from 4
    )

    metrics_style = ParagraphStyle(
        "MetricsStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=10,  # Reduced from 12
        # textColor=colors.HexColor("#f6f2f7"),
        textColor=colors.red,
        leading=14,  # Reduced from 16
        spaceAfter=3,  # Reduced from 4
        leftIndent=20
    )

    highlight_style = ParagraphStyle(
        "HighlightStyle",
        parent=styles["BodyText"],
        fontName="PoppinsBold",
        fontSize=14,
        # textColor=colors.HexColor("#c969f5"),
        textColor=colors.yellow,
        leading=16,
        spaceBefore=12,
        spaceAfter=12,
        alignment=1
    )

    growth_text_style = ParagraphStyle(
        "HighlightStyle",
        parent=styles["BodyText"],
        fontName="Poppins",
        fontSize=14,
        # textColor=colors.HexColor("#c969f5"),
        textColor=colors.black,
        leading=16,
        spaceBefore=12,
        spaceAfter=12,
        alignment=1
    )

    # Background and divider functions remain the same
    def draw_fancy_background(canvas, doc):
        canvas.setFillColor(colors.black)
        canvas.rect(0, 0, A4[0], A4[1], fill=1)

        if doc.page > 0:
            canvas.setFillColor(colors.HexColor("#6292cc"))
            canvas.setFont("Anton", 12)
            page_num = f"Page {doc.page}"
            canvas.drawString(A4[0] - 72, 30, page_num)
            canvas.setStrokeColor(colors.HexColor("#6292cc"))
            canvas.line(A4[0] - 82, 25, A4[0] - 40, 25)

    def create_divider():
        drawing = Drawing(A4[0] - 100, 15)  # Reduced height
        line = Line(0, 7, A4[0] - 100, 7)
        line.strokeColor = colors.HexColor("#6292cc")
        line.strokeWidth = 1
        drawing.add(line)
        return drawing

    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Top-left: Guideline logo
    c.drawImage("https://taippa.com/wp-content/uploads/2025/03/guideline_ai_logo_new-1.jpeg", 40, height - 130, width=170, height=150, mask='auto')
    
    c.setFont("Switzer", 16)
    c.setFillColor(colors.HexColor('#081956'))
    c.drawString(width - 200, height - 40, user_details.get("organization_name"))
    c.drawImage("https://taippa.com/wp-content/uploads/2025/04/globe.png", width - 200, height - 60, width=10, height=10, mask='auto')
    c.setFont("Poppins", 10)
    c.setFillColor(colors.HexColor('#0761fd'))
    c.drawString(width - 185, height - 60, user_details.get("organization_website"))
    c.setFillColor(colors.HexColor('#0761fd'))
    c.drawImage("https://taippa.com/wp-content/uploads/2025/05/email.jpeg", width - 200, height - 80, width=8, height=8, mask='auto')
    c.drawString(width - 185, height - 80, user_details.get("email"))

    # # Top-right: Contact Info
    # c.setFont("Poppins", 16)
    # c.setFillColor(colors.HexColor('#081956'))
    # c.drawString(width - 160, height - 40, user_details.get("organization_name"))

    # c.setFont("Poppins", 10)
    # c.setFillColor(colors.HexColor('#0761fd'))
    # c.drawString(width - 160, height - 55, user_details.get("organization_website"))
    # c.setFillColor(colors.black)
    # c.drawString(width - 160, height - 70, user_details.get("email"))

    # Center: MBC logo (above box if you wish)
    # c.drawImage("https://taippa.com/wp-content/uploads/2025/03/guideline_ai_logo_new-1.jpeg", width / 2 - 50, height - 240, width=100, height=40, mask='auto')

    # White rounded rectangle for description
    box_width = width - 160
    box_height = 400  # Height remains the same
    box_x = (width - box_width) / 2  # This centers the box horizontally
    box_y = (height - box_height) / 2

    c.setFillColor(colors.HexColor('#f6f4f1'))
    c.roundRect(box_x, box_y, box_width, box_height, radius=10, fill=1, stroke=0)
    print(f"\n\n--------- Adding Company logo -------\n\n")
    # Insert second logo inside box (e.g., left-aligned)
    second_logo_url = "https://taippa.com/wp-content/uploads/2025/04/image-13.png"
    second_logo_url = user_details.get('organization_logo')
    logo_width = 120
    logo_height = 120
    logo_x_center = box_x + (box_width - logo_width) / 2
    logo_y = box_y + box_height - logo_height - 10

    c.drawImage(second_logo_url, logo_x_center, logo_y, width=logo_width, height=logo_height, mask='auto')

    print(f"\n\n----------Adding icebreaker-------\n\n")
    # Description Text
    styles = getSampleStyleSheet()
    desc_style = ParagraphStyle(
        'desc',
        parent=styles['Normal'],
        fontName='Switzer',
        fontSize=18,
        leading=22,
        alignment=4,
        textColor=colors.HexColor("#0c1c59")
    )
    organization_short_description = user_details.get("organization_short_description")
    # print(f"organization_short_description: {organization_short_description}")
    if organization_short_description not in ["",None]:
        ice_breaker_content = ice_breaker_generator(organization_short_description)
        ice_breaker_message = Paragraph(ice_breaker_content, ice_breaker_style)
    
    # else:
    text = """
    <b>MBC Group</b>, formerly known as Middle East Broadcasting Center, is a Saudi media conglomerate based in the Riyadh region.
    Launched in London in 1991, the company moved its headquarters to Dubai in 2002 and to Riyadh in 2022.
    It is majority owned by the Saudi government-operated Public Investment Fund.
    """
    text = ice_breaker_content
    # Frame for text (adjusted below logo)
    frame_margin_top = 150
    frame = Frame(box_x + 10, box_y + 10, box_width - 20, box_height - frame_margin_top, showBoundary=0)
    frame.addFromList([Paragraph(text, desc_style)], c)
    print(f"\n\n-------- Adding Guideline Logo -------\n\n")
    # Bottom image
    c.drawImage("https://taippa.com/wp-content/uploads/2025/03/logo_guideline.png", width / 2 - 50, -10, width=150, height=120, mask='auto')

    c.save()
    return 
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Title of the white paper
    c.setFont("Helvetica-Bold", 20)
    c.drawString(100, 750, "Title of the White Paper")

    # Subtitle
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.grey)
    c.drawString(100, 730, "Subtitle or brief description of the white paper")

    # Content header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 700, "Introduction")
    
    # Content
    c.setFont("Helvetica", 12)
    text = """This is a sample white paper document generated using ReportLab.
    
    You can use this template to generate your own content. The document can include 
    various sections like introduction, methodology, findings, and conclusions.
    
    ReportLab allows you to create complex PDFs programmatically, making it a great 
    tool for generating reports, invoices, or white papers."""
    
    c.drawString(100, 670, text.split("\n")[0])
    y_position = 650
    
    for line in text.split("\n")[1:]:
        c.drawString(100, y_position, line)
        y_position -= 15
    
    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.grey)
    c.drawString(100, 50, "Generated by ReportLab - White Paper Document")
    
    # Save the PDF
    c.save()
    
    return 
    content = []

    # Get user details
    name = user_details.get('name', 'there')
    job_title = user_details.get('title', 'professional')
    industry = user_details.get('organization_industry', 'Real Estate')
    country = user_details.get('country', 'United Arab Emirates')
    company = user_details.get('organization_name','TAIPPA')
    if industry in ['Unknown', '']:
        industry = 'Real Estate'

    # Add title and introduction

    # content.append(Paragraph(f"15-Days Sales Improvement Planner for {company}", main_title))
    content.append(create_divider())
    content.append(Spacer(1, 0.1 * inch))  # Reduced spacing

    greeting = Paragraph(f"Hi {name},", greeting_style)
    print(f"user details: {user_details.keys()}")
    organization_short_description = user_details.get("organization_short_description")
    # print(f"organization_short_description: {organization_short_description}")
    if organization_short_description not in ["",None]:
        ice_breaker_content = ice_breaker_generator(organization_short_description)
        ice_breaker_message = Paragraph(ice_breaker_content, ice_breaker_style)
    # else:
    #     message = Paragraph(f"Breakthrough sales growth starts here: A powerful 15-day blueprint to revolutionize your {job_title} strategy at {company} and drive exceptional results.", ice_breaker_style)
    message_text = "Breakthrough sales growth starts here!"
    message = Paragraph(message_text, ice_breaker_style)  # <- Wrap it properly
    
    img1 = Img(user_details.get('organization_logo'))
    img1.drawWidth = 200  # Set image width
    img1.drawHeight = 100  # Set image height
   
    # images=[img1,img2,img3,img4,img5,img6]
    counter=1
    image_index=0
    content.append(img1)
    content.append(greeting)
    content.append(ice_breaker_message)

    # content.append(Paragraph(f"Hi {name},", greeting_style))
    # content.append(Paragraph(f"Breakthrough sales growth starts here: A powerful 15-day blueprint to revolutionize your {job_title} strategy and drive exceptional results.",ice_breaker_style))
    content.append(Spacer(1, 0.2 * inch))  # Reduced spacing
    content.append(Spacer(1, 0.2 * inch))

    # Create the PDF with reduced margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.5 * inch,  # Reduced from 0.6
        rightMargin=0.5 * inch,  # Reduced from 0.6
        topMargin=0.6 * inch,  # Reduced from 0.8
        bottomMargin=0.5 * inch  # Reduced from 0.6
    )
    print(f"\n -- Building document --\n")
    doc.build(content, onFirstPage=draw_fancy_background, onLaterPages=draw_fancy_background)
    print(f"PDF generated and saved at {output_path}")
    print(f"Successfully generated PDF")
    return
    personalized_planner = generate_personalized_planner(user_details)
    print(f"--------------------Personalized planner : {personalized_planner}------------------")
    formatted_content = content_formatting_json(personalized_planner)
    print(f"--------------------Formatted content : {formatted_content}------------------")
    # print(f"\n-------formatted_content --------: {formatted_content}")
    personalized_planner = json.loads(formatted_content)

    img1 = Img(image_path[9])
    img1.drawWidth = 500  # Set image width
    img1.drawHeight = 200  # Set image height
    # content.append(img)
    img2 = Img(image_path[10])
    img2.drawWidth = 500  # Set image width
    img2.drawHeight = 200  # Set image height
    # content.append(img)
    img3 = Img(image_path[11])
    img3.drawWidth = 500  # Set image width
    img3.drawHeight = 200  # Set image height
    # content.append(img)

    img4 = Img(image_path[12])
    img4.drawWidth = 500  # Set image width
    img4.drawHeight = 200  # Set image height
    # content.append(img)

    img5 = Img(image_path[13])
    img5.drawWidth = 500  # Set image width
    img5.drawHeight = 200  # Set image height
    # content.append(img)

    img6 = Img(image_path[14])
    img6.drawWidth = 500  # Set image width
    img6.drawHeight = 200  # Set image height

    images=[img1,img2,img3,img4,img5,img6]
    counter=1
    image_index=0
    content.append(images[image_index])
    content.append(Spacer(1, 0.2 * inch))
    image_index=1
    print(f"Items: {personalized_planner.items()}")
    for day, details in personalized_planner.items():
        print(f"---here---")
        print(day)
        # Add Day heading
        content.append(Spacer(1, 0.2 * inch))
        print(day)
        content.append(Paragraph(day, planner_title_style))

        # # Add Action Items
        if 'Action items' in details:
            for item in details['Action items']:
                content.append(CheckboxItem(item, checkbox_size=12, space_between=8))
                # content.append(Spacer(1, 0.1 * inch))
                # checkbox = CheckboxItem(item, checkbox_size=12, space_between=8)
                # table = Table([[checkbox, Paragraph(item, metrics_style)]])
                # content.append(KeepTogether(table))
                # content.append(Paragraph(f"• {item}", metrics_style))

        # Add some spacing between days
        content.append(Spacer(1, 0.2 * inch))
        content.append(Spacer(1, 0.2 * inch))
        content.append(Spacer(1, 0.2 * inch))
        if counter % 3 == 0 and counter!=15:
            # content.append(Spacer(1, 0.2 * inch))
            content.append(images[image_index])
            content.append(Spacer(1, 0.2 * inch))
            image_index+=1
        counter+=1
    print('Completed the checklist generation')
    # content.append(Spacer(1, 0.2 * inch))
    # content.append(images[-1])
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    content.append(Spacer(1, 0.2 * inch))
    growth_text = Paragraph(f"Accelerate Your Growth with Taippa", greeting_style_2)
    growth_text_2 = Paragraph(f"Take your business to the next level with our exclusive strategies "
                   "and tools designed for high-impact growth. Join us for a "
                   "<b>free demo</b> and explore how Taippa can empower your client "
                   "acquisition and revenue acceleration.", growth_text_style)
    growth_text_3 = Paragraph("📩 Book Your Free Demo Today!", planner_title_style_2)

    # # Create a Table with the content
    table_data = [[growth_text], [growth_text_2], [growth_text_3]]
    table = Table(table_data, colWidths=[500])  # Adjust width as needed

    # Apply style to the table
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),  # Background color
        ('BOX', (0, 0), (-1, -1), 1, colors.black),     # Border around the table
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),            # Align text to the top
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),          # Center align content horizontally
        ('TOPPADDING', (0, 0), (-1, -1), 20),           # Add padding to the top of each cell
        ('BOTTOMPADDING', (0, 0), (-1, -1), 20),        # Add padding to the bottom of each cell
        ('LEFTPADDING', (0, 0), (-1, -1), 20),          # Add padding to the left of each cell
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),         # Add padding to the right of each cell
    ])
    table.setStyle(table_style)
    table.keepTogether = True
    # Add the table to your content
    content.append(table)

    # Create the PDF with reduced margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=0.5 * inch,  # Reduced from 0.6
        rightMargin=0.5 * inch,  # Reduced from 0.6
        topMargin=0.6 * inch,  # Reduced from 0.8
        bottomMargin=0.5 * inch  # Reduced from 0.6
    )
    doc.build(content, onFirstPage=draw_fancy_background, onLaterPages=draw_fancy_background)
    print(f"PDF generated and saved at {output_path}")

def get_image_path():
    try:
        table = airtable_obj(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, CLIENT_INFO_TABLE_NAME)
        attachment_column="company_lead_magnet_images"
        print(table)
        print(AIRTABLE_API_KEY)
        return get_dynamic_images(table,'recHwMDeb62Kgiqx1',attachment_column)
    except Exception as e:
        print(f"Error occured at {__name__} while retrieving the images")

# def generate_lead_magnet_pdf(email,linkedin_url):
#     try:
#         user_details = collect_information(linkedin_url)
#         print(f" User details: {user_details}")
#         if user_details is None:
#             return "No user details found"
#         # print(user_details)
#         print(f" Directory path for pdf: {os.path.dirname(os.path.abspath(__file__))}")
#         output_path = os.path.join(SCRIPT_DIR,"pdf/lead_magnet_personalized.pdf")
#         first_pager = os.path.join(SCRIPT_DIR,"pdf/first_page.pdf")
#         last_pager = os.path.join(SCRIPT_DIR,"pdf/last_page.pdf")
#         company_name = user_details.get('organization_name','your company')
#         final_pdf = os.path.join(SCRIPT_DIR,f"pdf/15-day Sales Booster for {company_name}.pdf")
#         # image_path = get_image_path()
#         # print(f"Image path: {image_path}")
#         create_personalized_pdf(user_details,output_path)
#         # print("Successfully created lead magnet pdf")
#         # embed_existing_pdf(output_path, first_pager, last_pager,final_pdf)
#         # print("Sending lead magnet email..")
#         # email_status = send_lead_magnet_email(email,user_details,final_pdf)
#         # print("Successfully sent lead magnet email")
#         # print(email_status)
#         # return {"Status":email_status}
        

#         return {"Status":"Successfully created lead magnet pdf"}
#     except Exception as e:
#         print(f"Exception occured at {__name__} while generating the lead magnet pdf : {e}")
#         return "Oops! It seems our server is a bit busy right now. Please try again shortly."
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_authenticated_drive_service():
    creds = None
    token_path = os.path.join(PICKLE_DIR,'token.pickle')

    # Load saved credentials
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials, raise error (PythonAnywhere has no GUI)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("No valid credentials found and cannot run local server on PythonAnywhere.")
            raise Exception("Token missing. Please generate 'token.pickle' locally and upload to PythonAnywhere.")

        # Save credentials for next time
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

from pypdf import PdfReader, PdfWriter

def merge_pdfs_with_appendix(main_pdf_path, appendix_pdf_path, output_pdf_path):
    writer = PdfWriter()

    # Read the main personalized PDF
    main_pdf = PdfReader(main_pdf_path)
    for page in main_pdf.pages:
        writer.add_page(page)

    # Read the appendix PDF to be added from page 2
    appendix_pdf = PdfReader(appendix_pdf_path)
    for page in appendix_pdf.pages:
        writer.add_page(page)

    # Write the combined PDF
    with open(output_pdf_path, 'wb') as f_out:
        writer.write(f_out)

def normalize_linkedin(url: str) -> str:
    """
    Convert all LinkedIn URLs to a normalized format:
      - force https
      - remove www
      - remove trailing slash
    """
    if not url:
        return url

    url = url.strip()
    # force https
    url = url.replace("http://", "https://")
    # remove www.
    url = url.replace("https://www.", "https://")
    # remove trailing slash
    url = url.rstrip("/")

    return url

def generate_lead_magnet_pdf(email, linkedin_url):
    try:
        user_details = collect_information(linkedin_url)
        if user_details is None:
            return "No user details found"

        print(f"User details: {user_details}")

        output_path = os.path.join(SCRIPT_DIR, "pdf/lead_magnet_personalized.pdf")
        create_personalized_pdf(user_details, output_path)
        # Path to appendix PDF
        appendix_pdf_path = os.path.join(SCRIPT_DIR, "pdf/main_content.pdf")
        merged_pdf_path = os.path.join(SCRIPT_DIR, "pdf/lead_magnet_merged.pdf")

        # Merge personalized PDF with appendix starting from second page
        merge_pdfs_with_appendix(output_path, appendix_pdf_path, merged_pdf_path)

        # Use merged PDF as final output
        output_path = merged_pdf_path

        # 1. Upload to Google Drive
        drive_service = get_authenticated_drive_service()
        file_metadata = {"name": f"Lead Magnet - {linkedin_url}.pdf"}
        media = MediaFileUpload(output_path, mimetype="application/pdf")
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        file_id = uploaded_file.get("id")

        # 2. Make file public
        drive_service.permissions().create(
            fileId=file_id,
            body={"role": "reader", "type": "anyone"},
        ).execute()

        # 3. Generate direct download URL
        drive_url = f"https://drive.google.com/uc?id={file_id}&export=download"
        print(f"Drive URL: {drive_url}")

        # 4. Update Airtable
        airtable_update_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/outreach_guideline"
        headers = {
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        }
        # print("Querying Airtable with:")
        # print(json.dumps({
        #     "filterByFormula": f"{{linkedin_url}} = {json.dumps(linkedin_url)}"
        # }, indent=2))
        # Normalize lookup URL
        lookup_url = normalize_linkedin(linkedin_url)

        find_response = requests.get(
            airtable_update_url,
            headers=headers,
            params={
                "filterByFormula": f"{{linkedin_profile_url}} = {json.dumps(lookup_url)}"
            },
        )

        print("Searching for:", lookup_url)
        print("Airtable returned:", find_response.json())

        records = find_response.json().get("records", [])
        if not records:
            print("No matching record found in Airtable.")
            return "No matching Airtable record"
        # First: find the record by linkedin_url
        # find_response = requests.get(
        #     airtable_update_url,
        #     headers=headers,
        #     params={
        #         "filterByFormula": f"FIND({json.dumps(linkedin_url)}, {{linkedin_profile_url}})"
                
        #     },
        # )
        # records = find_response.json().get("records", [])
        # if not records:
        #     print("No matching record found in Airtable.")
        #     return "No matching Airtable record"

        record_id = records[0]["id"]

        # Then: patch the record
        update_payload = {
            "fields": {
                "lead_magnet_pdf": drive_url
            }
        }

        update_response = requests.patch(
            f"{airtable_update_url}/{record_id}",
            headers=headers,
            json=update_payload,  # send as JSON
        )

        print(f"Airtable update response: {update_response.text}")

        return {"Status": "PDF created and uploaded to Airtable"}

    except Exception as e:
        print(f"Exception occurred while generating the lead magnet PDF: {e}")
        return "Server error. Please try again later."

def test_run():
    try:
        output_pdf = "lead_magnet_personalized.pdf"
        user_id = "shiblashilu@gmail.com"
        linkedin_url = "http://www.linkedin.com/in/galeapatricia"
        generate_lead_magnet_pdf(user_id,linkedin_url)
        return {"Status":"Successfully created lead magnet pdf"}
    except Exception as e:
        print(f"Exception occured at {__name__} while generating the lead magnet pdf : {e}")

if __name__=="__main__":
    output_pdf = "lead_magnet_personalized.pdf"
    # user_id for testing
    user_id = "nadia@cgnet.ae"
    user_id = "timofey.borzov@vtbcapital.com"
    user_id = "shiblashilu@gmail.com"
    linkedin_url = "https://www.linkedin.com/in/nikhil-rajput-1a0b4a1b/"
    generate_lead_magnet_pdf(user_id,linkedin_url)
    # print(f"PDF generated and saved at {output_pdf}")
    # print("Raw metrics:", metrics)