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

def query_anthropic_with_tools(prompt: str, api_key: str) -> str:
    """Query Anthropic with tool use support."""
    client = Anthropic(api_key=api_key)
    print("[news_agent] Querying Anthropic with model claude-sonnet-4-20250514...")
    
    messages = [{"role": "user", "content": prompt}]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
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
            messages=messages
        )
        
        print("[news_agent] Received response from Anthropic")
        
        # Check if there's a text response
        text_content = None
        for block in response.content:
            if hasattr(block, 'text'):
                text_content = block.text
                break
        
        if response.stop_reason == "end_turn":
            if text_content:
                return text_content
            raise ValueError("No text content in final response")
        
        if response.stop_reason == "tool_use":
            # Add assistant's response to messages
            messages.append({"role": "assistant", "content": response.content})
            
            # Process tool calls
            tool_results = []
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'tool_use':
                    print(f"[news_agent] Processing tool call: {block.name} with query: {block.input.get('query', 'unknown')}")
                    # Execute the tool (placeholder for actual web search)
                    tool_result = f"Search results for: {block.input.get('query', 'unknown')}"
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_result
                    })
            
            # Add tool results to messages
            messages.append({"role": "user", "content": tool_results})
        else:
            raise ValueError(f"Unexpected stop reason: {response.stop_reason}")

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
    html_body = query_anthropic_with_tools(prompt, anthropic_api_key)

    print("[news_agent] Preparing email content...")
    send_email(subject, html_body, gmail_address, recipient_email, gmail_app_password)
    print("[news_agent] Morning news digest complete.")

if __name__ == "__main__":
    main()
