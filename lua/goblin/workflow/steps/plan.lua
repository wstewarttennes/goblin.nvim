local Popup = require("nui.popup")
local Layout = require("nui.layout")

local M = {}

--- TODO: This should take the input of the previous step and create a "Plan".
---       The plan should be a list of steps that the user can execute to update the codebase based on the input provided.
---       The plan is saved to an array of steps and returned by the step to be passed to the next step.
---       The plan is displayed in a popup window.

M.start_plan = function(step, continue_workflow, update_output, input)
  local popup_one, popup_two = Popup({
    enter = true,
    border = "single",
  }), Popup({
    border = "double",
  })

  local prompt = nil
  if step["prompt"] then
    prompt = step["plan"]
  else
    prompt = [[
      You are an AI programming assistant helping to create a plan of action based on the user's input.
      The input is provided.
      The plan should be a list of steps that the user can execute to update the codebase based on the input provided.
    ]]
  end


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
