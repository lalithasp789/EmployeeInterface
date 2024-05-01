from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from sentence_transformers import SentenceTransformer
import openai
import configparser
from qdrant_client import QdrantClient
import streamlit as st
from streamlit_chat import message
from streamlit_feedback import streamlit_feedback
from pymongo import MongoClient
from urllib.parse import quote_plus




st.set_page_config(initial_sidebar_state='expanded', page_title="HR Q&A Bot")

config = configparser.ConfigParser()
config.read(r'config.ini')
openai_api_key = st.secrets['openai_api_key']
pinecone_api_key = st.secrets['pinecone_api_key']
openai.api_key = openai_api_key
#####
mongodb_password = st.secrets['mongodb_password']
mongodb_username = st.secrets['mongodb_username']

mongopassword = quote_plus(mongodb_password)
connection_string = f"mongodb+srv://{mongodb_username}:{mongopassword}@cluster0.s4bz1ci.mongodb.net/?retryWrites=true&w=majority"

try:
    client = MongoClient(connection_string)
    db = client['hr_chatbot']
    collection = db['feedback']
except Exception as e:
    print(f"An error occurred while connecting to MongoDB: {e}")

####

from langchain.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder
)

qdrant_url = st.secrets['qdrant_url']
qdrant_api_key = st.secrets['qdrant_api_key']

client = QdrantClient(
url=qdrant_url,
api_key=qdrant_api_key)
collection_name="hr_chatbot" #collection_name="test_collection"

#model = SentenceTransformer('all-MiniLM-L6-v2')
model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

def find_match(input):
    input_em = model.encode(input).tolist()
    #input_em = model.encode(input).tolist()
    search_result = client.search(collection_name=collection_name,query_vector=input_em,limit=3)
    return search_result

def query_refiner(conversation, query):
    response = openai.Completion.create(
    model="gpt-3.5-turbo-instruct",
    prompt=f"Given the following user query and conversation log, formulate a question that would \
        be the most relevant to provide the user with an answer from a knowledge base.\n\nCONVERSATION \
            LOG: \n{conversation}\n\nQuery: {query}\n\nRefined Query:",
    temperature=0.5,
    max_tokens=256,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0
    )
    return response['choices'][0]['text']

def get_conversation_string():
    conversation_string = ""
    for i in range(len(st.session_state['responses'])-1):
        
        conversation_string += "Human: "+st.session_state['requests'][i] + "\n"
        conversation_string += "Bot: "+ st.session_state['responses'][i+1] + "\n"
    return conversation_string

st.header("HR Insight Bot: :blue[Your Virtual HR Assistant] :handshake: ")

if 'responses' not in st.session_state:
    st.session_state['responses'] = ["How can I assist you?"]

if 'requests' not in st.session_state:
    st.session_state['requests'] = []

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.4,max_tokens=500,verbose=True, openai_api_key=openai_api_key)

if 'buffer_memory' not in st.session_state:
            st.session_state.buffer_memory=ConversationBufferWindowMemory(k=3,return_messages=True)


system_msg_template = SystemMessagePromptTemplate.from_template(template="""Answer the question as truthfully as possible \
                                                                using the provided context, 
and if the answer is not contained within the text below, say 'I don't know, Please reach out to your HR Partner if the \
                                                                question is relevant to HR'
If answer contain a list, output as a bulleted or numbered list. If answer contain a table return as tab delimited. Also\
                                                                 respond only to the greetings eventhough \
                                                                the content is not available""")


human_msg_template = HumanMessagePromptTemplate.from_template(template="{input}")

prompt_template = ChatPromptTemplate.from_messages([system_msg_template, MessagesPlaceholder(variable_name="history"), human_msg_template])

conversation = ConversationChain(memory=st.session_state.buffer_memory, prompt=prompt_template, llm=llm, verbose=True)

# container for chat history
response_container = st.container()
# container for text box
textcontainer = st.container()

with textcontainer:
    query = st.chat_input("Please type your question here...!", key="input")
    if query:
        with st.spinner("typing..."):
            conversation_string = get_conversation_string()
            # st.code(conversation_string)
            refined_query = query_refiner(conversation_string, query)
            #st.subheader("Refined Query:")
            #st.write(refined_query)
            context = find_match(refined_query)
            # print(context)  
            response = conversation.predict(input=f"Context:\n {context} \n\n Query:\n{query}")
        st.session_state.requests.append(query)
        st.session_state.responses.append(response) 
        
with response_container:
    if st.session_state['responses']:
        
        for i in range(len(st.session_state['responses'])):
            message(st.session_state['responses'][i],key=str(i),avatar_style='avataaars')
            if i < len(st.session_state['requests']):
                message(st.session_state["requests"][i], is_user=True,key=str(i)+ '_user',avatar_style="initials",seed="LP")


st.warning("Contact IT Desk on 2222 or itsupportdesk@abc.com | Click www.abc.com to see the FAQ")

feedback = streamlit_feedback(feedback_type="thumbs", optional_text_label="Please share your feedback") 

if feedback == None:
     ""
else:
     result = collection.insert_one(feedback)
