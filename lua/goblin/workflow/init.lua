local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event

local data = require("goblin.workflow.steps.data")
local plan = require("goblin.workflow.steps.plan")
local code = require("goblin.workflow.steps.code")
local push = require("goblin.workflow.steps.push")
local aider = require("goblin.workflow.steps.aider")
local replace_buffer = require("goblin.workflow.steps.replace_buffer")
local json = require("packages.dkjson.dkjson")

-- Module table
local M = {
  workflow = nil,
  current_step = 1,
  output = nil,
}

function splitString(str, char)
  local result = {} -- Initialize an empty table to store the arrays
  local index = 1   -- Initialize an index variable to keep track of the arrays in the table
  local start = 1   -- Initialize a start variable to keep track of the start index of each array

  -- Loop through each character in the string
  for i = 1, #str do
    -- Check if the current character is equal to the specified character
    if str:sub(i, i) == char then
      -- Add the array from the start index to the current index - 1 to the table
      result[index] = str:sub(start, i - 1)
      index = index + 1 -- Increment the index variable
      start = i + 1     -- Update the start index to the next character
    end
  end

  -- Add the remaining characters after the last specified character to the table
  result[index] = str:sub(start)

  return result -- Return the table of arrays
end

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
  local goblin_json_path = cwd .. "/.workflows.goblin.json"

  if file_exists(goblin_json_path) then
    return goblin_json_path
  else
    return nil
  end
end

-- Function to load and parse the .goblin.json file if it exists
local function load_goblin_json()
  local goblin_json_path = check_for_goblin_json()
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

local function pretty_print_table(tbl, indent)
  indent = indent or 0
  local toprint = string.rep(" ", indent) .. "{\n"
  indent = indent + 2
  for k, v in pairs(tbl) do
    toprint = toprint .. string.rep(" ", indent)
    if (type(k) == "number") then
      toprint = toprint .. "[" .. k .. "] = "
    elseif (type(k) == "string") then
      toprint = toprint .. k .. " = "
    end
    if (type(v) == "number") then
      toprint = toprint .. v .. ",\n"
    elseif (type(v) == "string") then
      toprint = toprint .. "\"" .. v .. "\",\n"
    elseif (type(v) == "table") then
      toprint = toprint .. pretty_print_table(v, indent + 2) .. ",\n"
    else
      toprint = toprint .. "\"" .. tostring(v) .. "\",\n"
    end
  end
  toprint = toprint .. string.rep(" ", indent - 2) .. "}"
  return toprint
end

local function print_table_to_buffer(tbl)
end

start = function(options)
  -- Example usage
  local goblin_config = load_goblin_json()

  vim.cmd [[
      highlight MyHighlightGroup ctermbg=grey guibg=grey
    ]]
  local popup_one, popup_two = Popup({
    enter = true,
    border = "single",
    buf_options = {
      modifiable = true,
      readonly = false,
    },
    win_options = {
      winhighlight = "Normal:Normal,FloatBorder:FloatBorder",
    },
  }), Popup({
    border = "double",
  })

  local layout = Layout(
    {
      position = "50%",
      size = {
        width = "90%",
        height = "90%",
      },
    },
    Layout.Box({
      Layout.Box(popup_one, { size = "40%" }),
      Layout.Box(popup_two, { size = "60%" }),
    }, { dir = "row" })
  )

  local current_dir = "row"

  popup_one:map("n", "r", function()
    if current_dir == "col" then
      layout:update(Layout.Box({
        Layout.Box(popup_one, { size = "40%" }),
        Layout.Box(popup_two, { size = "60%" }),
      }, { dir = "row" }))

      current_dir = "row"
    else
      layout:update(Layout.Box({
        Layout.Box(popup_two, { size = "60%" }),
        Layout.Box(popup_one, { size = "40%" }),
      }, { dir = "col" }))

      current_dir = "col"
    end
  end, {})

  layout:mount()

  vim.api.nvim_win_set_option(popup_two.winid, 'wrap', true)
  -- List of hashes
  local i = 0
  local hashed_issues = {}

  for key, value in pairs(goblin_config) do
    vim.api.nvim_buf_set_lines(popup_one.bufnr, i, i, false, { key })

    if value then
      hashed_issues[key] = value
    end

    if i == 0 then
      if value then
        -- Convert the table to a pretty string
        local pretty_str = pretty_print_table(value)

        -- Split the pretty string by new lines
        local lines = {}
        for s in pretty_str:gmatch("[^\r\n]+") do
          table.insert(lines, s)
        end

        -- Set the lines in the buffer
        vim.api.nvim_buf_set_lines(popup_two.bufnr, 0, -1, false, lines)
      end
      vim.api.nvim_win_set_cursor(0, { 1, 0 })
    end
    i = i + 1
  end

  -- Function to update the highlight
  local function update_highlight()
    -- Get the current cursor position
    local cursor_pos = vim.api.nvim_win_get_cursor(popup_one.winid)
    local line_number = cursor_pos[1] - 1

    local line_text = vim.api.nvim_buf_get_lines(popup_one.bufnr, line_number, line_number + 1, false)[1]

    vim.api.nvim_buf_set_lines(popup_two.bufnr, 0, -1, false, {})

    local value = hashed_issues[line_text]
    local pretty_str = pretty_print_table(value)

    -- Split the pretty string by new lines
    local lines = {}
    for s in pretty_str:gmatch("[^\r\n]+") do
      table.insert(lines, s)
    end

    vim.api.nvim_buf_set_lines(popup_two.bufnr, 0, -1, false, lines)
  end

  vim.api.nvim_buf_add_highlight(popup_one.bufnr, -1, "MyHighlightGroup", 0, 0, -1)
  vim.api.nvim_win_set_cursor(popup_one.winid, { 1, 0 })

  -- Set up autocmd to update highlight on cursor movement
  vim.api.nvim_create_autocmd("CursorMoved", {
    buffer = popup_one.bufnr,
    callback = update_highlight,
  })

  -- Function to handle Enter key press
  _G.handle_enter_key = function()
    -- Get the current cursor position
    local cursor_pos = vim.api.nvim_win_get_cursor(popup_one.winid)
    local line_number = cursor_pos[1] - 1

    -- Get the current line text
    local line_text = vim.api.nvim_buf_get_lines(popup_one.bufnr, line_number, line_number + 1, false)[1]
    M.workflow = hashed_issues[line_text]
    layout:unmount()
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

  vim.api.nvim_buf_set_keymap(popup_one.bufnr, 'n', '<CR>', ':lua handle_enter_key()<CR>',
    { noremap = true, silent = true })
end

start_workflow = function(args, options)
  -- Example usage
  local workflowName;
  if args and args[1] then
    workflowName = args[1]
  end

  local goblin_config = load_goblin_json()
  if goblin_config then
    M.workflow = goblin_config[workflowName]
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
    code.code(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "push" then
    push.push(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "aider" then
    aider.aider(step, M.continue_workflow, M.update_output, M.output)
  elseif step["type"] == "replace_buffer" then
    replace_buffer.run(step, M.continue_workflow, M.update_output, M.output)
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
M.start = start
M.start_workflow = start_workflow
M.continue_workflow = continue_workflow
M.update_output = update_output

return M
