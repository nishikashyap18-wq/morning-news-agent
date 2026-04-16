import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

from anthropic import Anthropic

def get_env_var(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    return value

def build_prompt(today_date: str) -> str:
    return (
        "You are a news digest assistant. Use the web search tool to find the top 5 news stories today "
        "across Business and Technology. For each story, provide a headline, source, 2-3 sentence summary, "
        "and a brief 'why it matters' section. Return the final result as clean HTML suitable for an email body. "
        "Include an introductory greeting, a separate section for each story, and a short closing. "
        "Do not include any explanation outside the HTML email content."
        f"\n\nDate: {today_date}\n"
    )

def query_anthropic(prompt: str, api_key: str) -> str:
    client = Anthropic(api_key=api_key)
    print("[news_agent] Querying Anthropic with model claude-sonnet-4-20250514...")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        temperature=0.2,
        tools=[
            {
                "name": "web_search_20250305",
                "description": "Search the web for current information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        }
                    },
                    "required": ["query"]
                }
            }
        ],
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    print("[news_agent] Received response from Anthropic")
    return extract_response_text(response)

def extract_response_text(response) -> str:
    if not hasattr(response, 'content'):
        raise ValueError("Unexpected Anthropic response format")
    
    parts = []
    for block in response.content:
        if hasattr(block, 'text'):
            parts.append(block.text)
    
    if parts:
        return "".join(parts)
    
    raise ValueError("Unable to extract text from Anthropic response")

def send_email(subject: str, html_body: str, sender: str, recipient: str, password: str) -> None:
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient

    html_part = MIMEText(html_body, "html")
    message.attach(html_part)

    print(f"[news_agent] Connecting to Gmail SMTP as {sender}...")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(sender, password)
        smtp.sendmail(sender, recipient, message.as_string())
    print(f"[news_agent] Email sent to {recipient}")

def main() -> None:
    print("[news_agent] Starting morning news digest process...")

    anthropic_api_key = get_env_var("ANTHROPIC_API_KEY")
    gmail_address = get_env_var("GMAIL_ADDRESS")
    gmail_app_password = get_env_var("GMAIL_APP_PASSWORD")
    recipient_email = get_env_var("RECIPIENT_EMAIL")

    eastern = ZoneInfo("America/New_York")
    today = datetime.now(tz=eastern)
    subject_date = today.strftime("%B %d, %Y")
    subject = f"Your Morning Digest — {subject_date}"

    prompt = build_prompt(subject_date)
    html_body = query_anthropic(prompt, anthropic_api_key)

    print("[news_agent] Preparing email content...")
    send_email(subject, html_body, gmail_address, recipient_email, gmail_app_password)
    print("[news_agent] Morning news digest complete.")

if __name__ == "__main__":
    main()