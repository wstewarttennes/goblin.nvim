local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event

local data = require("goblin.workflow.steps.data")
local plan = require("goblin.workflow.steps.plan")
local code = require("goblin.workflow.steps.code")
local push = require("goblin.workflow.steps.push")
local aider = require("goblin.workflow.steps.aider")
local json = require("packages.dkjson.dkjson")

-- Module table
local M = {
  workflow = nil,
  current_step = 1,
  output = nil,
}

function printTable(t, indent)
  indent = indent or 0
  local indentStr = string.rep("  ", indent)

  if type(t) ~= "table" then
    print(indentStr .. tostring(t))
    return
  end

  print(indentStr .. "{")
  for k, v in pairs(t) do
    local key = tostring(k)
    if type(v) == "table" then
      print(indentStr .. "  " .. key .. " = ")
      printTable(v, indent + 1)
    else
      print(indentStr .. "  " .. key .. " = " .. tostring(v))
    end
  end
  print(indentStr .. "}")
end

-- Function to read file content
local function read_file(file_path)
  local file = io.open(file_path, "r")
  if not file then
    return nil, "Could not open file: " .. file_path
  end
  local content = file:read("*all")
  file:close()
  return content
end

-- Function to decode JSON from file
local function load_json_from_file(file_path)
  local content, err = read_file(file_path)
  if not content then
    return nil, err
  end
  local decoded_table, pos, err = json.decode(content, 1, nil)
  if err then
    return nil, "JSON Decode Error: " .. err
  end
  return decoded_table
end

-- Function to get the current working directory
local function get_current_working_directory()
  return vim.fn.getcwd()
end

-- Function to check if a file exists
local function file_exists(file_path)
  local file = io.open(file_path, "r")
  if file then
    file:close()
    return true
  else
    return false
  end
end

-- Function to check for .goblin.json in the current working directory
local function check_for_goblin_json()
  local cwd = get_current_working_directory()
  local goblin_json_path = cwd .. "/.goblin.json"

  if file_exists(goblin_json_path) then
    return goblin_json_path
  else
    return nil
  end
end

-- Function to load and parse the .goblin.json file if it exists
local function load_goblin_json()
  local goblin_json_path = check_for_goblin_json()
  print(goblin_json_path)
  if goblin_json_path then
    local file_content = read_file(goblin_json_path)
    if file_content then
      local decoded_table, pos, err = json.decode(file_content, 1, nil)
      if err then
        vim.api.nvim_err_writeln("JSON Decode Error: " .. err)
        return nil
      end
      return decoded_table
    end
  else
    vim.api.nvim_echo(
      { { "No .goblin.json file found in your project, defaulting to Neovim configuration.", "WarningMsg" } }, false, {})
    return nil
  end
end


-- Forward declarations for functions to resolve scoping issues
local run_step
local start_workflow
local continue_workflow
local update_output

update_output = function(output)
  M.output = output
end

start_workflow = function(options)
  -- Example usage
  local goblin_config = load_goblin_json()
  if goblin_config then
    M.workflow = goblin_config["workflow"]
  else
    M.workflow = options["workflow"]
  end
  if M.workflow then
    for key, step in pairs(M.workflow) do
      if step["order"] == 1 then
        step["type"] = key
        run_step(step)
      end
    end
    M.current_step = 2
  else
    print("No workflow found")
  end
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
    code.code(step, M.continue_workflow, M.update_output)
  elseif step["type"] == "push" then
    push.push(step, M.continue_workflow, M.update_output)
  elseif step["type"] == "aider" then
    aider.aider(step, M.continue_workflow, M.update_output)
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
