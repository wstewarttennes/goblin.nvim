# goblin.nvim

Goblin.nvim is a Neovim plugin that allows you to create custom workflows with a focus on automating 
the process of  updating codebases. This lets you to do things similar to Github Copilot Workflow, 
where the workflow needs context and access to code beyond a single buffer.

Goblin works by following a series of steps that you define in a configuration file. Each step
takes the input from the previous step and returns the output for the next step. Steps can be
anything theoretically, but the default steps are data, plan, code, and push.



### Default Configuration / Steps

1. Data: Define input sources. The input source is something like a Github Issue or a Jira ticket 
         that should provide the context for what needs to be updated in the codebase. The data step
         also has you select one of the input sources as the output of the step. You can also define
         a manual entry step that lets you enter the data when the workflow runs.
         Currently Goblin supports the following input sources:
           • Jira
           <!-- • Github -->
           <!-- • Manual Entry -->

      Output: Buffer with selected data from the input source.


2. Plan: 

      Output: Buffer with plan formatted in markdown.

3. Code:

      Output: Buffer with code changes formatted in markdown.

4. Push:

      Output: ??



### Installation

Goblin requires a few dependencies to work.
Install with your plugin manager.


### Setup

1. Determine where your input is coming from. 
2. Define workflow
3. Add .goblin file to your project directory.
4. Add configuration to .goblin file (see Workflows)

### .goblin

The .goblin file is a configuration file that allows you to specify the workflow for your project. It should be 
placed in the root of your project directory. The following values can be set in the .goblin file:

workflow: This is the workflow that your goblin will follow. It is a list of steps that your goblin will follow. 
          Each step has a name, description, type, and extra field. The name is the name of the step, the description
          is a description of the step, the type is the type of step (data, plan, code, accept), and the extra field is
          any extra information needed for the step.

credentials: This is the credentials that your goblin will use to access the input source. It is a list of credentials
             that your goblin will use to access the input source. Each credential has a name and a value. The name is the
             name of the credential, and the value is the value of the credential.

### Example File

##### Connects list various integration points needed for various workflow steps.

connections = [{
   "name": "jira",
   "username": "username",
   "password": "password" # do not store in plain text, load from a secure location
}, {
   "name": "github",
   "username": "username",
   "password": "password" # do not store in plain text, load from a secure location
}]

##### A workflow is a list of steps your Goblin will delicately follow. Workflows are defined in your .goblin file.  An example workflow looks like this. 

workflow = [{
   name: "Select Jira Ticket",
   description: "Grab current jira tickets and list them. Select one to start.",
   type: "data",
   extra: {
      "source": "jira",
      "project_id": "1234"
   },
   ui: "select",
},
{
   name: "Plan",
   description: "Plan the work that needs to be done.",
   type: "plan",
   extra: {
      ""
   },
   ui: "textbox",
},
{
   name: "Code",
   description: "",
   type: "code",
   ui: "code",
},
{
   name: "Create Github PR",
   description: "Review the changes and create a github PR.",
   type: "create"
   ui: "confirm"
}]


### Default Step Types

data: 
   input: none (calls data source or manual entry)
   ouptut: data

plan: creates a plan of action from a buffer
   input: buffer 
   output: table of plan steps

code: uses a plan or a buffer to generate code changes
   input: buffer or table of plan steps
   ouptut: table of file changes

push: pushes a tables of file changes to a remote git repository
   input: table of file changes
   output: success or error


##### Other Step Types

aider: takes a buffer and an instruction and runs it through aider 
   input: buffer
   ouput: aider will update files and git commit the changed files


### Custom Steps 

You can define your own steps either via your goblin configuration (less configurable)
or via a lua file in your plugin directory. If you create a lua file for a step that you
think is particularly useful, please submit a pull request to add it to the available steps.
Keep in mind that any step should clean up its own messes - make sure to close any open popups 
or other UI elements when the step is complete.

### Other Workflows

Other workflows are available in the workflows folder in this repository. If you have a workflow
you think is useful, please submit a pull request to add it to the available workflows.

### UI Types

select
textbox
code
confirm


{
   "name": this is the name of the workflow step, it can be anything
   "description": if you want to add some more info
   "type": this is the type of step, it can be "data", "plan", "code", "accept"
   "extra": this is used for any extra info needed for each workflow step. For example, for data steps, you might need to specify the source of the data. 
}

### Running the Plugin

I map `:Goblin` to <Leader>ai which initiates the workflow. Browse/Search through issues and select one to start. From there, your default 
workflow will dictate how the algorithm proceeds.


### Generalized LLAMA Ingestion, Indexing, Embedding, Storing

The purpose of this plugin is to speed up development time, and this includes
the training of the 



### SOURCES
These are sources that I used to create this plugin. Some might be flawed, use incorrect 
assumptions, or be flat out wrong. If you see mistakes, let me know :) 

How Copilot Works Under The Hood
https://thakkarparth007.github.io/copilot-explorer/posts/copilot-internals.html



CrewAI: Autonomous AI Agents 
https://www.crewai.com/


### Common Questions

Q: why is it called Goblin?
A: the menace that will take your (my) job

Q: what does it do?
A: it allows you to create workflows via easy configuration that you can use to develop code. i imagine
   as editors evolve, they will continue to abstract the complexity of the problems we work on. goblin
   is an attempt at that abstraction.




