local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event

local M = {}

M.code = function(step, continue_workflow, update_output, input)
  print("ENTER to code.")
  local popup_one, popup_two = Popup({
    enter = true,
    border = "single",
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
end

return M
