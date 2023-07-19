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

os.environ["OPENAI_API_KEY"] = "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"
os.environ["SERPAPI_API_KEY"] = "bc3a9cd7e7baf8c696e502082591f67a0b6b4c6b02a7513606c2b6fd890900e6"

from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.llms import OpenAI

llm = OpenAI(temperature=0.5)

from langchain.llms import OpenAI
from langchain import LLMChain
from langchain.prompts.prompt import PromptTemplate

# Chat specific components
from langchain.memory import ConversationBufferMemory

llm2 = OpenAI(temperature=0.2)

template2 = """
you are provided with a question asked by a Chatbot and its answer provied by a human your task is to evaluate the answer provided by the user based on the question asked and give a point between 1-5 and also give the reason for the evaluation

Chatbot: {question}
Human: {answer}

# Answer Completeness Validation
<% if len(human_answer.split()) < 3 %>
    Please provide a more complete answer.
<% end %>
"""

prompt2 = PromptTemplate(
    input_variables=["question", "answer"], 
    template=template2
)
#memory2 = ConversationBufferMemory(memory_key="chat_history")

llm_chain2 = LLMChain(
    llm=llm2, 
    prompt=prompt2, 
    verbose=True, 
)


q = "What is DevOps?"
a = "devops is a something"

evaluation = llm_chain2.predict(question=q ,answer=a)

def main():
    st.write(evaluation)
        

if __name__ == '__main__':
    main()