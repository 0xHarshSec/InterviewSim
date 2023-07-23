import os
import streamlit as st
from IPython.display import display, HTML
import openai
from dotenv import load_dotenv
display(HTML("<style>.container { width:90% !important; }</style>"))

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
serp_api_key = os.getenv("SERPAPI_API_KEY")

openai.api_key = openai_api_key
os.environ["SERPAPI_API_KEY"] = serp_api_key


from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI


from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts.prompt import PromptTemplate

# Chat specific components
from langchain.memory import ConversationBufferMemory

#Importing custom LLMs
import question as q
import eval as e

chat_history = ConversationBufferMemory(return_messages=True)
cnt = 0 

def ask_question(previous_question,previous_answer):
    question = q.generate_question(previous_question=previous_question,previous_answer=previous_answer)
    st.write(question)
    answer = st.input("Enter your answer")
    evaluation = e.evaluate_answer(question=question,answer=answer)
    previous_question = question
    previous_answer = answer
    if cnt == 5:
        return
    cnt+=1
    ask_question(previous_question,previous_answer)

def main():
    st.title("Chatbot with LangChain")
    
    ask_question("tell me about yourself","I am a devops engineer")
            
        

if __name__ == '__main__':
    main()