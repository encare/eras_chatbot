import pytest
import json
from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval, AnswerRelevancyMetric
from deepeval.dataset import EvaluationDataset

with open("results.json", "r") as f:
    results = json.load(f)

correctness = GEval(name="Correctness", criteria="Determine if the 'actual output' is correct based on the 'expected output'.", evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT])

dataset = EvaluationDataset(test_cases=[LLMTestCase(input=i["question"], actual_output=i["model_response"], expected_output=i["ground_truth"]) for i in results])

@pytest.mark.parametrize(
    "test_case",
    dataset,
)

def test_chatbot(test_case: LLMTestCase):
    assert_test(test_case, [correctness, AnswerRelevancyMetric(threshold=0.5)])

