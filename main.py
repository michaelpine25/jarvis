from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

message = client.messages.create(
  model="claude-sonnet-4-6",
  max_tokens=1024,
  messages=[{"role": "user", "content": "Say hello Jarvis!"}]
)

print(message.content[0].text)