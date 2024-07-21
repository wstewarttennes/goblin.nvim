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
  -- Get the current buffer
  local bufnr = vim.api.nvim_get_current_buf()
  local lines = vim.api.nvim_buf_get_lines(bufnr, 0, -1, false)

  -- Print the name of the current buffer
  update_output(lines)
end

return M
