from transformers import (
    GPT2Tokenizer,
    TextDataset,
    DataCollatorForLanguageModeling,
    GPT2LMHeadModel,
    Trainer,
    TrainingArguments,
)
import os
import ast
import sys
from lupa import LuaRuntime

print("Summarizing Codebase")


def read_file(file_path):
    encodings = ["utf-8", "latin-1", "cp1252"]  # List of encodings to try
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        f"Could not decode file {file_path} with provided encodings"
    )


def extract_lua_functions(lua_code):
    lua = LuaRuntime(unpack_returned_tuples=True)
    function_names = []
    try:
        # Run the Lua code in a protected environment
        lua.execute(lua_code)
        # Retrieve global function names
        globals_table = lua.globals()
        for key in globals_table.keys():
            if lua.type(globals_table[key]) == "function":
                function_names.append(key)
    except Exception as e:
        print(f"Error parsing Lua code: {e}")
    return function_names


def summarize_codebase(directory):
    summary = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".lua"):
                file_path = os.path.join(root, file)
                try:
                    file_content = read_file(file_path)
                    if file.endswith(".py"):
                        tree = ast.parse(file_content, filename=file)
                        summary[file_path] = {
                            "functions": [
                                node.name
                                for node in ast.walk(tree)
                                if isinstance(node, ast.FunctionDef)
                            ],
                            "classes": [
                                node.name
                                for node in ast.walk(tree)
                                if isinstance(node, ast.ClassDef)
                            ],
                        }
                    if file.endswith(".lua"):
                        functions = extract_lua_functions(file_content)
                        summary[file_path] = {
                            "functions": functions,
                            "classes": [],  # Lua doesn't have classes like Python
                        }
                except (UnicodeDecodeError, RuntimeError) as e:
                    print(f"Skipping file {file_path} due to error: {e}")
    return summary


if __name__ == "__main__":
    codebase_directory = sys.argv[1]
    print(f"Summarizing Codebase: {codebase_directory}")
    summary = summarize_codebase(codebase_directory)
    for file, details in summary.items():
        print(f"File: {file}")
        print(f"Classes: {details['classes']}")
        print(f"Functions: {details['functions']}\n")
# Prep Data
# tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
#
#
# def load_dataset(file_path, tokenizer):
#     return TextDataset(tokenizer=tokenizer, file_path=file_path, block_size=128)
#
#
# def create_data_collator(tokenizer):
#     return DataCollatorForLanguageModeling(
#         tokenizer=tokenizer,
#         mlm=False,
#     )
#
#
# train_dataset = load_dataset("path/to/your/codebase.txt", tokenizer)
#
#
# data_collator = create_data_collator(tokenizer)
#
# # Define Model
#
# model = GPT2LMHeadModel.from_pretrained("gpt2")
#
# # Train Model
# training_args = TrainingArguments(
#     output_dir="./results",
#     overwrite_output_dir=True,
#     num_train_epochs=3,
#     per_device_train_batch_size=2,
#     save_steps=10_000,
#     save_total_limit=2,
# )
#
# trainer = Trainer(
#     model=model,
#     args=training_args,
#     data_collator=data_collator,
#     train_dataset=train_dataset,
# )
#
#
# trainer.train()
#
# # Evaluate Model
# eval_results = trainer.evaluate()
# print(f"Perplexity: {eval_results['eval_loss']}")
#
# # Save model
# model.save_pretrained("path/to/save/model")
# tokenizer.save_pretrained("path/to/save/tokenizer")
#
#
# # Inference
#
# tokenizer = GPT2Tokenizer.from_pretrained("path/to/save/tokenizer")
# model = GPT2LMHeadModel.from_pretrained("path/to/save/model")
#
# inputs = tokenizer("Your input code here", return_tensors="pt")
# outputs = model.generate(inputs["input_ids"], max_length=50)
# print(tokenizer.decode(outputs[0], skip_special_tokens=True))
