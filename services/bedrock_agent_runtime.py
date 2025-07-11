import boto3
from botocore.exceptions import ClientError

def invoke_agent(agent_id, agent_alias_id, session_id, prompt):
    try:
        client = boto3.session.Session().client(service_name="bedrock-agent-runtime")
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime/client/invoke_agent.html
        def generate():
            output_text = ""
            citations = []
            trace = {}
            response = client.invoke_agent(
                agentId=agent_id,
                agentAliasId=agent_alias_id,
                enableTrace=True,
                sessionId=session_id,
                inputText=prompt,
                streamingConfigurations={'streamFinalResponse': True} # Enable streaming for final response
            )

            has_guardrail_trace = False
            chunk_received = False

            # Iterate over the response stream
            for event in response.get("completion"): 
                # Combine the chunks to get the output text
                if "chunk" in event:
                    chunk = event["chunk"]
                    output_text += chunk["bytes"].decode()
                    if "attribution" in chunk:
                        citations = citations + chunk["attribution"]["citations"]
                    chunk_received = True

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
                
                if chunk_received:
                    yield {
                        "output_text": output_text,
                        "citations": citations,
                        "trace": trace
                    }

            # Finalize the output after all chunks are processed
            yield {
                "output_text": output_text,
                "citations": citations,
                "trace": trace
            }

    except ClientError as e:
        raise
    
    return generate()
