import langsmith

client = langsmith.Client()

# Clone the dataset to your tenant to use it
public_dataset = (
    "https://smith.langchain.com/public/326674a6-62bd-462d-88ae-eea49d503f9d/d"
)
client.clone_public_dataset(public_dataset)

from langsmith.schemas import Example, Run


def check_import(run: Run, example: Example) -> dict:
    imports = run.outputs.get("imports")
    try:
        exec(imports)
        return {"key": "import_check", "score": 1}
    except Exception:
        return {"key": "import_check", "score": 0}


def check_execution(run: Run, example: Example) -> dict:
    imports = run.outputs.get("imports")
    code = run.outputs.get("code")
    try:
        exec(imports + "\n" + code)
        return {"key": "code_execution_check", "score": 1}
    except Exception:
        return {"key": "code_execution_check", "score": 0}

def predict_base_case(example: dict):
    """Context stuffing"""
    solution = code_gen_chain.invoke(
        {"context": concatenated_content, "messages": [("user", example["question"])]}
    )
    solution_structured = code_gen_chain.invoke([("code", solution)])
    return {"imports": solution_structured.imports, "code": solution_structured.code}


def predict_langgraph(example: dict):
    """LangGraph"""
    graph = app.invoke({"messages": [("user", example["question"])], "iterations": 0})
    solution = graph["generation"]
    return {"imports": solution.imports, "code": solution.code}


from langsmith.evaluation import evaluate

# Evaluator
code_evalulator = [check_import, check_execution]

# Dataset
dataset_name = "test-LCEL-code-gen"

# Run base case
experiment_results_ = evaluate(
    predict_base_case,
    data=dataset_name,
    evaluators=code_evalulator,
    experiment_prefix=f"test-without-langgraph-{expt_llm}",
    max_concurrency=2,
    metadata={
        "llm": expt_llm,
    },
)

# Run with langgraph
experiment_results = evaluate(
    predict_langgraph,
    data=dataset_name,
    evaluators=code_evalulator,
    experiment_prefix=f"test-with-langgraph-{expt_llm}-{flag}",
    max_concurrency=2,
    metadata={
        "llm": expt_llm,
        "feedback": flag,
    },
)
