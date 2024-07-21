local api = require("nvim-tree.api")

local M = {}


M.run = function(step, continue_workflow, update_output, input)
  -- Input should be current buffer and instructions
  -- Take input and pass to ai
  local prompt = nil
  if step["prompt"] then
    prompt = step["prompt"]
  else
    prompt = [[


    ]]
  end

  -- Make sure model is specified
  if not step["model"] then
    return "No model specified"
  end
  -- Take input and pass to the ai along with prompt
end

return M
