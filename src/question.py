import os
import streamlit as st
from IPython.display import display, HTML
display(HTML("<style>.container { width:90% !important; }</style>"))
import openai
from dotenv import load_dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain

load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")
# serp_api_key = os.getenv("SERPAPI_API_KEY")

os.environ["OPENAI_API_KEY"] = "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"
# os.environ["SERPAPI_API_KEY"] = serp_api_key

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

llm = OpenAI(temperature=0.5)

from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts.prompt import PromptTemplate

# Chat specific components
from langchain.memory import ConversationBufferMemory

#LLM 1
question_llm = OpenAI(temperature=0.4)

question_template = """
You are an unbiased interviewer chatbot.
Given a previously asked question and its answer as it is provided by the human, generate a intelligent interview question that would be suitable to ask next.

Previous Question: {previous_question}
Human: {previous_answer}
"""

question_prompt = PromptTemplate(
    input_variables=["previous_question","previous_answer"], 
    template=question_template
)


generate_question_chain = LLMChain(
    llm=question_llm, 
    prompt=question_prompt, 
    verbose=True,
)



# q = "What is DevOps?"
# a = "DevOps is a set of practices that combines software development (Dev) and IT operations (Ops) to improve collaboration, communication, and automation in delivering software products."

def generate_question(previous_question,previous_answer):
    return generate_question_chain.predict(previous_question=previous_question,previous_answer=previous_answer)

generate_question("tell me about yourself","I am a devops engineer")