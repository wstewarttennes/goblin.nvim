local Popup = require("nui.popup")
local Layout = require("nui.layout")

local M = {}

M.push = function(step, continue_workflow, update_output, input)
  print("ENTER to push data to " .. step["source"])
end

return M
