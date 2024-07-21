local jira = require("goblin.workflow.steps.data.jira")
local linear = require("goblin.workflow.steps.data.linear")
local manual_input = require("goblin.workflow.steps.data.input")
local buffer = require("goblin.workflow.steps.data.buffer")

local M = {}

M.get_data = function(step, continue_workflow, update_output, input)
  -- HANDLE JIRA
  if step["source"] == "jira" then
    jira.run(step, continue_workflow, update_output, input)
  end
  -- HANDLE JIRA
  if step["source"] == "linear" then
    linear.run(step, continue_workflow, update_output, input)
  end
  -- HANDLE Manual Input
  if step["source"] == "input" then
    input.run(step, continue_workflow, update_output, input)
  end
  -- HANDLE Current Buffer
  if step["source"] == "buffer" then
    buffer.run(step, continue_workflow, update_output, input)
  end

  if step["sources"] then
    for i, source in ipairs(step["sources"]) do
      if source == "jira" then
        jira.run(step, continue_workflow, update_output, input)
      end
      if source == "linear" then
        linear.run(step, continue_workflow, update_output, input)
      end
      if source == "input" then
        manual_input.run(step, continue_workflow, update_output, input)
      end
      if source == "buffer" then
        buffer.run(step, continue_workflow, update_output, input)
      end
    end
  end
end

return M
