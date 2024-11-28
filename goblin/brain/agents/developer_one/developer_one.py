from langchain_core.messages import HumanMessage, SystemMessage, RemoveMessage, trim_messages
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END
from bs4 import BeautifulSoup as Soup
from langchain_community.document_loaders.recursive_url_loader import RecursiveUrlLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from brain.agents.agent import BaseAgent, GraphState

############################
# Developer One: Buisveesz # (credit to https://www.fantasynamegenerators.com/goblin-names.php for Goblin names)
############################


class DeveloperOne(BaseAgent):

    # 1. Input: 
    #        codebase_path
    #        prompt
    #        testing_commands (list of tests for cli to run to ensure code is working)
    #        documentation url (optional)
    #        buffer with any additional instructions
    def __init__(self, data):
        self.codebase_path = data["codebase_path"]
        self.handle_codebase()

        self.documentation_url = data["documentation_url"]
        self.handle_documentation_url()

        self.additional_buffer = data["additional_buffer"]
        if self.additional_buffer:
            self.handle_additional_buffer()

        self.prompt = data["prompt"]

        self.testing_commands = data["testing_commands"]

        self.max_iterations = 3

        self.create_graph()

    
    def handle_codebase(self):
        # need to injest codebase and output useful information
        # treesitter parse
        pass


    def handle_documentation_url(self):
        # Handle Documentation URL
        loader = RecursiveUrlLoader(
            url=self.documentation_url, max_depth=20, extractor=lambda x: Soup(x, "html.parser").text
        )
        docs = loader.load()

        # Sort the list based on the URLs and get the text
        d_sorted = sorted(docs, key=lambda x: x.metadata["source"])
        d_reversed = list(reversed(d_sorted))
        self.concatenated_content = "\n\n\n --- \n\n\n".join(
            [doc.page_content for doc in d_reversed]
        )

    def handle_additional_buffer(self):
        pass

    def create_graph(self):

        workflow = StateGraph(GraphState)

        # Define the nodes
        workflow.add_node("plan", self.plan)  # generation solution
        workflow.add_node("find_files", self.find_files)  # generation solution
        workflow.add_node("generate", self.generate)  # generation solution
        workflow.add_node("check_code", self.code_check)  # check code
        workflow.add_node("reflect", self.reflect)  # reflect

        # Build graph
        workflow.add_edge(START, "plan")
        workflow.add_edge("plan", "find_files")
        workflow.add_edge("find_files", "generate")
        workflow.add_edge("generate", "reflect")
        workflow.add_edge("reflect", "generate")
        workflow.add_edge("generate", "check_code")
        workflow.add_conditional_edges(
            "check_code",
            self.decide_to_finish,
            {
                "end": END,
                "reflect": "reflect",
                "plan": "plan",
            },
        )
        app = workflow.compile()

    def run(self):

        # Grader prompt
        code_gen_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a coding assistant with expertise in LCEL, LangChain expression language. \n 
            Here is a full set of LCEL documentation:  \n ------- \n  {context} \n ------- \n Answer the user 
            question based on the above provided documentation. Ensure any code you provide can be executed \n 
            with all required imports and variables defined. Structure your answer with a description of the code solution. \n
            Then list the imports. And finally list the functioning code block. Here is the user question:""",
                ),
                ("placeholder", "{messages}"),
            ]
        )



        expt_llm = "gpt-4-0125-preview"
        llm = ChatOpenAI(temperature=0, model=expt_llm)
        self.code_gen_chain = code_gen_prompt | llm.with_structured_output(code)
        question = "How do I build a RAG chain in LCEL?"
        self.solution = self.code_gen_chain.invoke({"context":self.concatenated_content,"messages":[("user",question)]})

    def plan(self):
        code_gen_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a coding assistant with expertise in LCEL, LangChain expression language. \n 
            Here is a full set of LCEL documentation:  \n ------- \n  {context} \n ------- \n Answer the user 
            question based on the above provided documentation. Ensure any code you provide can be executed \n 
            with all required imports and variables defined. Structure your answer with a description of the code solution. \n
            Then list the imports. And finally list the functioning code block. Here is the user question:""",
                ),
                ("placeholder", "{messages}"),
            ]
        )



        expt_llm = "gpt-4-0125-preview"
        llm = ChatOpenAI(temperature=0, model=expt_llm)
        self.code_gen_chain = code_gen_prompt | llm.with_structured_output(code)
        question = "How do I build a RAG chain in LCEL?"
        self.solution = self.code_gen_chain.invoke({"context":self.concatenated_content,"messages":[("user",question)]})

    def find_files(self):
        pass

    def generate(self, state: GraphState):
        """
        Generate a code solution

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """

        print("---GENERATING CODE SOLUTION---")

        # State
        messages = state["messages"]
        iterations = state["iterations"]
        error = state["error"]

        # We have been routed back to generation with an error
        if error == "yes":
            messages += [
                (
                    "user",
                    "Now, try again. Invoke the code tool to structure the output with a prefix, imports, and code block:",
                )
            ]

        # Solution
        code_solution = self.code_gen_chain.invoke(
            {"context": self.concatenated_content, "messages": messages}
        )
        messages += [
            (
                "assistant",
                f"{code_solution.prefix} \n Imports: {code_solution.imports} \n Code: {code_solution.code}",
            )
        ]

        # Increment
        iterations = iterations + 1
        return {"generation": code_solution, "messages": messages, "iterations": iterations}


    def code_check(self, state: GraphState):
        """
        Check code

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, error
        """

        print("---CHECKING CODE---")

        # State
        messages = state["messages"]
        code_solution = state["generation"]
        iterations = state["iterations"]

        # Get solution components
        imports = code_solution.imports
        code = code_solution.code

        # Check imports
        try:
            exec(imports)
        except Exception as e:
            print("---CODE IMPORT CHECK: FAILED---")
            error_message = [("user", f"Your solution failed the import test: {e}")]
            messages += error_message
            return {
                "generation": code_solution,
                "messages": messages,
                "iterations": iterations,
                "error": "yes",
            }

        # Check execution
        try:
            exec(imports + "\n" + code)
        except Exception as e:
            print("---CODE BLOCK CHECK: FAILED---")
            error_message = [("user", f"Your solution failed the code execution test: {e}")]
            messages += error_message
            return {
                "generation": code_solution,
                "messages": messages,
                "iterations": iterations,
                "error": "yes",
            }

        # No errors
        print("---NO CODE TEST FAILURES---")
        return {
            "generation": code_solution,
            "messages": messages,
            "iterations": iterations,
            "error": "no",
        }


    def reflect(self, state: GraphState):
        """
        Reflect on errors

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation
        """

        print("---GENERATING CODE SOLUTION---")

        # State
        messages = state["messages"]
        iterations = state["iterations"]
        code_solution = state["generation"]

        # Prompt reflection

        # Add reflection
        reflections = self.code_gen_chain.invoke(
            {"context": self.concatenated_content, "messages": messages}
        )
        messages += [("assistant", f"Here are reflections on the error: {reflections}")]
        return {"generation": code_solution, "messages": messages, "iterations": iterations}



    def decide_to_finish(self, state: GraphState):
        """
        Determines whether to finish.

        Args:
            state (dict): The current graph state

        Returns:
            str: Next node to call
        """
        error = state["error"]
        iterations = state["iterations"]

        if error == "no" or iterations == self.max_iterations:
            print("---DECISION: FINISH---")
            return "end"
        else:
            print("---DECISION: RE-TRY SOLUTION---")
            if self.flag == "reflect":
                return "reflect"
            else:
                return "generate"











