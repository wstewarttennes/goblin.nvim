
############################
# Developer Two: ????? # (credit to https://www.fantasynamegenerators.com/goblin-names.php for Goblin names)
############################


# Developer Two allows for selecting multiple providers to do the planning/coding.

class DeveloperTwo():

    def __init__(self, data):

        # PROVIDER: "plandex"
        self.provider = data["provider"] if "provider" in data else "plandex"

        # CONTEXT: {"files": [], "text": ""}
        self.context = data["context"] if "context" in data else None

        # TASK: {"text": ""}
        self.task = data["task"] if "task" in data else None

    
    # Run Developer Task
    def run(self):
        if not self.provider:
            return "No provider"

        if self.provider == "plandex":
            self.run_plandex()
        elif self.provider == "aider":
            self.run_aider()
        elif self.provider == "avante":
            self.run_avante()

    # PLANDEX
    def run_plandex(self):
        # plandex new
        # plandex load some-file.ts another-file.ts
        # plandex load src/components -r # load a whole directory
        # plandex load src --tree # load a directory layout (file names only)
        # plandex load src/**/*.ts # load files matching a glob pattern
        # plandex load https://raw.githubusercontent.com/plandex-ai/plandex/main/README.md # load the text content of a url
        # plandex load images/mockup.png # load an image
        # plandex tell "add a new line chart showing the number of foobars over time to components/charts.tsx"
        pass

    # AIDER
    def run_aider(self):
        pass

    # AVANTE
    def run_avante(self):
        pass
    
    










