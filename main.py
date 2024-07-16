import os
import pathlib
import textwrap

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown
from dotenv import load_dotenv

def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))

if __name__ == "__main__":
  load_dotenv()
  GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
  DISCORD_API_KEY = os.getenv('DISCORD_API_KEY')

  genai.configure(api_key=GOOGLE_API_KEY)

  model = genai.GenerativeModel('gemini-1.5-flash')

  prompt = input("What we asking gemini G? ")

  response = model.generate_content(prompt)
  
  print(response.text)
