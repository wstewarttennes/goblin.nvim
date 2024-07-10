local jira = require("goblin.workflow.steps.data.jira")
local linear = require("goblin.workflow.steps.data.linear")

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
end

return M
