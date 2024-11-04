from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, MessagesState
import datetime
from tools import book_appointment, get_next_available_appointment, cancel_appointment
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage

# Import ChatGroq instead of OpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set the Groq API key
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")

# Initialize the Groq model with the necessary parameters
llm = ChatGroq(model="llama-3.1-70b-versatile", temperature=0.5)

# Track conversation messages
CONVERSATION = []

# Function to process and respond to user messages
def receive_message_from_caller(message):
    CONVERSATION.append(HumanMessage(content=message, type="human"))
    state = {
        "messages": CONVERSATION,
    }
    print(state)
    new_state = caller_app.invoke(state)
    CONVERSATION.extend(new_state["messages"][len(CONVERSATION):])

# Edge function for determining conversation continuation
def should_continue_caller(state: MessagesState):
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return "end"
    else:
        return "continue"

# Node function to call the Groq model
def call_caller_model(state: MessagesState):
    state["current_time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    response = caller_model.invoke(state)
    return {"messages": [response]}

# List of tools for managing appointments
caller_tools = [book_appointment, get_next_available_appointment, cancel_appointment]
tool_node = ToolNode(caller_tools)

# Define prompt template for the assistant
caller_pa_prompt = """You are a personal assistant and need to help the user to book or cancel appointments. You should check the available appointments before booking anything. Be extremely polite, almost to the point of rudeness.
Current time: {current_time}
"""

# Define the chat prompt template
caller_chat_template = ChatPromptTemplate.from_messages([
    ("system", caller_pa_prompt),
    ("placeholder", "{messages}"),
])

# Bind the tools to the Groq model and set up the model pipeline
caller_model = caller_chat_template | llm.bind_tools(caller_tools)

# Initialize the graph and workflow
caller_workflow = StateGraph(MessagesState)

# Add nodes for the workflow
caller_workflow.add_node("agent", call_caller_model)
caller_workflow.add_node("action", tool_node)

# Define conditional edges for the workflow
caller_workflow.add_conditional_edges(
    "agent",
    should_continue_caller,
    {
        "continue": "action",
        "end": END,
    },
)
caller_workflow.add_edge("action", "agent")

# Set the entry point and compile the workflow
caller_workflow.set_entry_point("agent")
caller_app = caller_workflow.compile()
