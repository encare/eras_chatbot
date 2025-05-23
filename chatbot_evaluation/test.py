import os
import json
import uuid
from dotenv import load_dotenv
import streamlit as st
import boto3
from botocore.exceptions import ClientError

load_dotenv()

agent_id = os.getenv("BEDROCK_AGENT_ID")
agent_alias_id = os.getenv("BEDROCK_AGENT_ALIAS_ID")
session_id = str(uuid.uuid4())

with open("testset.json", "r") as f:
    testset = json.load(f)



def invoke_agent(agent_id, agent_alias_id, session_id, prompt):
    try:
        client = boto3.session.Session().client(service_name="bedrock-agent-runtime")
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
        response = client.invoke_agent(
            agentId=agent_id,
            agentAliasId=agent_alias_id,
            enableTrace=True,
            sessionId=session_id,
            inputText=prompt,
        )

        output_text = ""
        citations = []
        trace = {}

        has_guardrail_trace = False
        for event in response.get("completion"):
            # Combine the chunks to get the output text
            if "chunk" in event:
                chunk = event["chunk"]
                output_text += chunk["bytes"].decode()
                if "attribution" in chunk:
                    citations = citations + chunk["attribution"]["citations"]

            # Extract trace information from all events
            if "trace" in event:
                for trace_type in ["guardrailTrace", "preProcessingTrace", "orchestrationTrace", "postProcessingTrace"]:
                    if trace_type in event["trace"]["trace"]:
                        mapped_trace_type = trace_type
                        if trace_type == "guardrailTrace":
                            if not has_guardrail_trace:
                                has_guardrail_trace = True
                                mapped_trace_type = "preGuardrailTrace"
                            else:
                                mapped_trace_type = "postGuardrailTrace"
                        if trace_type not in trace:
                            trace[mapped_trace_type] = []
                        trace[mapped_trace_type].append(event["trace"]["trace"][trace_type])

    except ClientError as e:
        raise

    return {
        "output_text": output_text,
        "citations": citations,
        "trace": trace
    }


results = []

for i in testset["test_pairs"]:
    question = i["question"]
    ground_truth = i["ground_truth"]
    response = invoke_agent(
        agent_id,
        agent_alias_id,
        session_id,
        question
    )
    results.append({
        "question": question,
        "ground_truth": ground_truth,
        "model_response": response["output_text"]
    })
    
with open("results.json", "w") as f:
    json.dump(results, f, indent=4)
    print("Results saved to results.json")
