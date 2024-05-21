local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event

local data = require("goblin.workflow.steps.data")
local plan = require("goblin.workflow.steps.plan")
local code = require("goblin.workflow.steps.code")
local push = require("goblin.workflow.steps.push")
local aider = require("goblin.workflow.steps.aider")

-- Module table
local M = {
  workflow = nil,
  current_step = 1,
  output = nil,
}

-- Calculate dimensions as 90% of the current screen size
-- local screen_width = vim.o.columns
-- local screen_height = vim.o.lines
-- local width = math.floor(screen_width * 0.9)
-- local height = math.floor(screen_height * 0.9)

-- Forward declarations for functions to resolve scoping issues
local run_step
local start_workflow
local continue_workflow
local update_output

update_output = function(output)
  M.output = output
end

run_step = function(step)
  if not step then
    print("No step found")
    return
  elseif not step["type"] then
    print("No step type found")
  end
  if step["type"] == "data" then
    data.get_data(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "plan" then
    plan.start_plan(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "code" then
    code.code(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "push" then
    push.push(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "aider" then
    aider.aider(step, M.continue_workflow, M.update_output, M.output)
  end
end

start_workflow = function(options)
  M.workflow = options["workflow"]
  if M.workflow then
    for key, value in pairs(M.workflow) do
      if value["order"] == 1 then
        value["type"] = key
        run_step(value)
      end
    end
    M.current_step = 2
  else
    print("No workflow found")
  end
end

continue_workflow = function()
  if not M.workflow then
    print("Run GoblinRun first")
    return
  else
    for key, value in pairs(M.workflow) do
      if M.current_step == value["order"] then
        value["type"] = key
        run_step(value)
      end
    end
    M.current_step = M.current_step + 1
  end
end

-- Expose module functions
M.run_step = run_step
M.start_workflow = start_workflow
M.continue_workflow = continue_workflow
M.update_output = update_output

return M
