import os
import streamlit as st
from IPython.display import display, HTML
display(HTML("<style>.container { width:90% !important; }</style>"))

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain

# Prompt templates for dynamic values
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate, 
    HumanMessagePromptTemplate
)

from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

os.environ["OPENAI_API_KEY"] = "OPEN_API_KEY"
os.environ["SERPAPI_API_KEY"] = "SERP"

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
llm1 = OpenAI(temperature=0.4)
llm2 = OpenAI(temperature=0.4)

template1 = """
Given the chat history and the answer provided by the user for the previous question, generate a intelligent interview question that would be suitable to ask next.

{chat_history}

Previous Question: {previous_question}
Human: {human_answer}
"""

prompt1 = PromptTemplate(
    input_variables=["chat_history","previous_question","human_answer"], 
    template=template1
)

#memory = ConversationBufferMemory(memory_key="chat_history")

llm_chain1 = LLMChain(
    llm=llm1, 
    prompt=prompt1, 
    verbose=True,
)



q = "What is DevOps?"
a = "DevOps is a set of practices that combines software development (Dev) and IT operations (Ops) to improve collaboration, communication, and automation in delivering software products."

question = llm_chain1.predict(chat_history=memory2,previous_question=q,human_answer=a)
print(question)

def main():
    st.write(question)
        

if __name__ == '__main__':
    main()