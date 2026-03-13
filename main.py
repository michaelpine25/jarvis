from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()

conversation_history = []

system_prompt = """You are Jarvis, a helpful and intelligent personal desk assistant. 
You are concise, friendly, and professional. You help with questions, tasks, 
reminders, and anything else the user needs. Keep responses brief and conversational 
since they will be spoken out loud."""

def chat(user_input):
  conversation_history.append({"role": "user", "content": user_input})
  
  response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=system_prompt,
    messages=conversation_history
  )
  
  assistant_message = response.content[0].text
  conversation_history.append({"role": "assistant", "content": assistant_message})
  
  return assistant_message

while True:
  user_input = input("You: ")
  if user_input.lower() in ["exit", "quit", "bye"]:
    print("Jarvis: Goodbye!")
    break
  response = chat(user_input)
  print(f"Jarvis: {response}")