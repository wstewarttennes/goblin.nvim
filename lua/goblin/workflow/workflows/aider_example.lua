local config = {
  data = {
    order = 1,
    source = "jira",
    source_options = {
      domain = "**.atlassian.net",
      user = "",
      token = "",
      params = {
        project = "**",
        -- sprint = "current", -- TODO
      }
    },
  },
  aider = {
    order = 2,
    prompt = [[
      You are an AI programming assistant. Follow the user's requirements carefully & to the letter.
    ]]
  },
}
local meta = {
  name = "Aider"
}
