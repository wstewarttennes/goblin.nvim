local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event
local jira = require("goblin.integrations.jira")

local M = {}

function printTable(tbl, indent)
  if not indent then indent = 0 end
  local toprint = string.rep(" ", indent) .. "{\n"
  indent = indent + 2
  for k, v in pairs(tbl) do
    toprint = toprint .. string.rep(" ", indent)
    if (type(k) == "number") then
      toprint = toprint .. "[" .. k .. "] = "
    elseif (type(k) == "string") then
      toprint = toprint .. k .. "= "
    end
    if (type(v) == "number") then
      toprint = toprint .. v .. ",\n"
    elseif (type(v) == "string") then
      toprint = toprint .. "\"" .. v .. "\",\n"
    elseif (type(v) == "table") then
      toprint = toprint .. printTable(v, indent + 2) .. ",\n"
    else
      toprint = toprint .. "\"" .. tostring(v) .. "\",\n"
    end
  end
  toprint = toprint .. string.rep(" ", indent - 2) .. "}"
  return toprint
end

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

M.run = function(step, continue_workflow, update_output, input)
  --
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

  jira.setup({
    domain = step["source_options"]["domain"],
    user = step["source_options"]["user"],
    token = step["source_options"]["token"],
    key = step["source_options"]["project"]
  })
  local params = step["source_options"]["params"]
  local jira_res = jira.get_issues(params)
  -- Define a table
  if not jira_res then
    print("No issues found")
    return
  end


  vim.api.nvim_win_set_option(popup_two.winid, 'wrap', true)
  -- List of hashes
  local i = 0
  local hashed_issues = {}
  for key, value in pairs(jira_res["issues"]) do
    local line_string = value["key"]
    vim.api.nvim_buf_set_lines(popup_one.bufnr, i, i, false, { line_string })

    if value["fields"]["description"] then
      hashed_issues[value["key"]] = value
    end

    if i == 0 then
      -- for k, v in pairs(value["fields"]) do
      --
      -- end
      if value["fields"]["description"] then
        local split = splitString(value["fields"]["description"], "\n")
        vim.api.nvim_buf_set_lines(popup_two.bufnr, 0, 0, false, { "Description" })
        for j = 1, #split do
          vim.api.nvim_buf_set_lines(popup_two.bufnr, j, j, false, { split[j] })
        end
      end
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

    local description = hashed_issues[line_text]["fields"]["description"]
    local split = splitString(description, "\n")
    vim.api.nvim_buf_set_lines(popup_two.bufnr, 0, 0, false, { "Description" })
    for j = 1, #split do
      vim.api.nvim_buf_set_lines(popup_two.bufnr, j, j, false, { split[j] })
    end

    -- Clear existing highlights
    vim.api.nvim_buf_clear_namespace(popup_one.bufnr, -1, 0, -1)

    -- Add the highlight to the current line
    vim.api.nvim_buf_add_highlight(popup_one.bufnr, -1, "MyHighlightGroup", line_number, 0, -1)
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
    print("Enter key pressed on line: " .. line_text)
    layout:unmount()
    local output_buffer = [[
      The following describes the issue that we are working on.
    ]]
    printTable(hashed_issues[line_text])
    update_output(output_buffer)
    continue_workflow()
  end

  vim.api.nvim_buf_set_keymap(popup_one.bufnr, 'n', '<CR>', ':lua handle_enter_key()<CR>',
    { noremap = true, silent = true })
end

return M
