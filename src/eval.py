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
openai_api_key = os.getenv("OPENAI_API_KEY")
serp_api_key = os.getenv("SERPAPI_API_KEY")

openai.api_key = openai_api_key
os.environ["SERPAPI_API_KEY"] = serp_api_key


from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

llm = OpenAI(temperature=0.5)

from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts.prompt import PromptTemplate

# Chat specific components
from langchain.memory import ConversationBufferMemory

eval_llm = OpenAI(temperature=0.2)

evaluation_template = """
you are provided with a question asked by a Chatbot and its answer provied by a human your task is to evaluate the answer provided by the user based on the question asked and give a point between 1-5 and also give the reason for the evaluation

Chatbot: {question}
Human: {answer}

# Answer Completeness Validation
<% if len(human_answer.split()) < 3 %>
    Please provide a more complete answer.
<% end %>
"""

evaluation_prompt = PromptTemplate(
    input_variables=["question", "answer"], 
    template=evaluation_template
)

evaluation_chain = LLMChain(
    llm=eval_llm, 
    prompt=evaluation_prompt, 
    verbose=True, 
)

# q = "What is DevOps?"
# a = "DevOps is a set of practices that combines software development (Dev) and IT operations (Ops) to improve collaboration, communication, and automation in delivering software products."


# evaluation = evaluation_chain.predict(question=q ,answer=a)

def evaluate_answer(question,answer):
    return evaluation_chain.predict(question=question ,answer=answer)
