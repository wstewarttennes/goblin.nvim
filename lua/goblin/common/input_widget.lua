local Input = require("nui.input")

return function(name, on_submit)
  local input = Input({
    zindex = 100,
    position = "50%",
    size = {
      width = 60,
    },
    relative = "editor",
    border = {
      style = "rounded",
      text = {
        top = " " .. name .. " ",
        top_align = "center",
      },
    },
    win_options = {
      winhighlight = "Normal:Normal,FloatBorder:FloatBorder",
    },
  }, {
    on_submit = on_submit,
  })

  return input
end
