import json
import os
from services import bedrock_agent_runtime
import streamlit as st
import uuid
from dotenv import load_dotenv
from streamlit import tabs

load_dotenv()

# Get config from environment variables
agent_id = st.secrets["BEDROCK_AGENT_ID"]
agent_alias_id = st.secrets["BEDROCK_AGENT_ALIAS_ID"]
ui_title = st.secrets.get("BEDROCK_AGENT_TEST_UI_TITLE", "Agents for Amazon Bedrock Test UI")
ui_icon = st.secrets.get("BEDROCK_AGENT_TEST_UI_ICON")

# Get config for the second chatbot
agent2_id = st.secrets["BEDROCK_AGENT2_ID"]
agent2_alias_id = st.secrets["BEDROCK_AGENT2_ALIAS_ID"]

# General page configuration and initialization
st.set_page_config(page_title=ui_title, page_icon=ui_icon, layout="wide")
st.title(ui_title)

# Initialize session state for both chatbots
if "chatbot1" not in st.session_state:
    st.session_state.chatbot1 = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "citations": [],
        "trace": {}
    }

if "chatbot2" not in st.session_state:
    st.session_state.chatbot2 = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "citations": [],
        "trace": {}
    }

# Function to reset session state for a specific chatbot
def reset_chatbot_state(chatbot_key):
    st.session_state[chatbot_key] = {
        "session_id": str(uuid.uuid4()),
        "messages": [],
        "citations": [],
        "trace": {}
    }

# Create tabs for the two chatbots
tab1, tab2 = st.tabs(["ERAS Essential Chatbot", "JIRA Customer Tickets Chatbot"])

# Chatbot 1 tab
with tab1:
    st.subheader("Chat with ERAS Essential Chatbot")
    if st.button("Reset ERAS Essential Chatbot"):
        reset_chatbot_state("chatbot1")

    for message in st.session_state.chatbot1["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if prompt := st.chat_input(key=1):
        st.session_state.chatbot1["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("...")
            response = bedrock_agent_runtime.invoke_agent(
                agent_id,
                agent_alias_id,
                st.session_state.chatbot1["session_id"],
                prompt
            )
            for result in response:
                output_text = result["output_text"]
                citations = result["citations"]
                trace = result["trace"]

                # Display streaming output
                placeholder.markdown(output_text, unsafe_allow_html=True)

            # Add citations to final response
            if len(citations) > 0:
                citation_num = 1
                num_citation_chars = 0
                citation_locs = ""
                for citation in citations:
                    end_span = citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 3
                    for retrieved_ref in citation["retrievedReferences"]:
                        citation_marker = f"[{citation_num}]"
                        output_text = output_text[:end_span + num_citation_chars] + citation_marker + output_text[end_span + num_citation_chars:]
                        
                        # Extract the file name from the S3 URI
                        s3_uri = retrieved_ref["location"]["s3Location"]["uri"]
                        file_name = s3_uri.split("/")[-1]  # Get the file name from the URI
                        
                        citation_locs = citation_locs + f"\n<br>{citation_marker} {file_name}"
                        citation_num += 1
                        num_citation_chars += len(citation_marker)
                    
                    output_text = output_text[:end_span + num_citation_chars] + "\n" + output_text[end_span + num_citation_chars:]
                    num_citation_chars += 1
                output_text = output_text + "\n" + citation_locs
            placeholder.markdown(output_text, unsafe_allow_html=True)
            st.session_state.chatbot1["messages"].append({"role": "assistant", "content": output_text})
            st.session_state.chatbot1["citations"] = citations
            st.session_state.chatbot1["trace"] = trace

# Chatbot 2 tab
with tab2:
    st.subheader("Chat with JIRA Customer Tickets Chatbot")
    if st.button("Reset JIRA Customer Tickets Chatbot"):
        reset_chatbot_state("chatbot2")

    for message in st.session_state.chatbot2["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"], unsafe_allow_html=True)

    if prompt := st.chat_input(key=2):
        st.session_state.chatbot2["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("...")
            response = bedrock_agent_runtime.invoke_agent(
                agent2_id,
                agent2_alias_id,
                st.session_state.chatbot2["session_id"],
                prompt
            )
            for result in response:
                output_text = result["output_text"]
                citations = result["citations"]
                trace = result["trace"]
                
                # Display streaming output
                placeholder.markdown(output_text, unsafe_allow_html=True)

            # Add citations to final response
            if len(citations) > 0:
                citation_num = 1
                num_citation_chars = 0
                citation_locs = ""
                for citation in citations:
                    end_span = citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 3
                    for retrieved_ref in citation["retrievedReferences"]:
                        citation_marker = f"[{citation_num}]"
                        output_text = output_text[:end_span + num_citation_chars] + citation_marker + output_text[end_span + num_citation_chars:]
                        
                        # Extract the file name from the S3 URI
                        s3_uri = retrieved_ref["location"]["s3Location"]["uri"]
                        file_name = s3_uri.split("/")[-1]  # Get the file name from the URI
                        
                        citation_locs = citation_locs + f"\n<br>{citation_marker} {file_name}"
                        citation_num += 1
                        num_citation_chars += len(citation_marker)
                    
                    output_text = output_text[:end_span + num_citation_chars] + "\n" + output_text[end_span + num_citation_chars:]
                    num_citation_chars += 1
                output_text = output_text + "\n" + citation_locs

            placeholder.markdown(output_text, unsafe_allow_html=True)
            st.session_state.chatbot2["messages"].append({"role": "assistant", "content": output_text})
            st.session_state.chatbot2["citations"] = citations
            st.session_state.chatbot2["trace"] = trace

trace_types_map = {
    "Pre-Processing": ["preGuardrailTrace", "preProcessingTrace"],
    "Orchestration": ["orchestrationTrace"],
    "Post-Processing": ["postProcessingTrace", "postGuardrailTrace"]
}

trace_info_types_map = {
    "preProcessingTrace": ["modelInvocationInput", "modelInvocationOutput"],
    "orchestrationTrace": ["invocationInput", "modelInvocationInput", "modelInvocationOutput", "observation", "rationale"],
    "postProcessingTrace": ["modelInvocationInput", "modelInvocationOutput", "observation"]
}

# Sidebar section for trace
with st.sidebar:
    st.title("Trace")

    # Show each trace types in separate sections
    step_num = 1
    for trace_type_header in trace_types_map:
        st.subheader(trace_type_header)

        # Organize traces by step similar to how it is shown in the Bedrock console
        has_trace = False
        for trace_type in trace_types_map[trace_type_header]:
            if trace_type in st.session_state.chatbot1["trace"]:
                has_trace = True
                trace_steps = {}

                for trace in st.session_state.chatbot1["trace"][trace_type]:
                    # Each trace type and step may have different information for the end-to-end flow
                    if trace_type in trace_info_types_map:
                        trace_info_types = trace_info_types_map[trace_type]
                        for trace_info_type in trace_info_types:
                            if trace_info_type in trace:
                                trace_id = trace[trace_info_type]["traceId"]
                                if trace_id not in trace_steps:
                                    trace_steps[trace_id] = [trace]
                                else:
                                    trace_steps[trace_id].append(trace)
                                break
                    else:
                        trace_id = trace["traceId"]
                        trace_steps[trace_id] = [
                            {
                                trace_type: trace
                            }
                        ]

                # Show trace steps in JSON similar to the Bedrock console
                for trace_id in trace_steps.keys():
                    with st.expander(f"Trace Step " + str(step_num), expanded=False):
                        for trace in trace_steps[trace_id]:
                            trace_str = json.dumps(trace, indent=2)
                            st.code(trace_str, language="json", line_numbers=trace_str.count("\n"))
                    step_num = step_num + 1
        if not has_trace:
            st.text("None")

    st.subheader("Citations")
    if len(st.session_state.chatbot1["citations"]) > 0:
        citation_num = 1
        for citation in st.session_state.chatbot1["citations"]:
            for retrieved_ref_num, retrieved_ref in enumerate(citation["retrievedReferences"]):
                with st.expander("Citation [" + str(citation_num) + "]", expanded=False):
                    citation_str = json.dumps({
                        "generatedResponsePart": citation["generatedResponsePart"],
                        "retrievedReference": citation["retrievedReferences"][retrieved_ref_num]
                    }, indent=2)
                    st.code(citation_str, language="json", line_numbers=trace_str.count("\n"))
                citation_num = citation_num + 1
    else:
        st.text("None")