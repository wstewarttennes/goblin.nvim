local config = {
  data = {
    order = 1,
    source = "jira",
    source_options = {
      domain = "**.atlassian.net",
      user = "**@**.com",
      token = "**",
      params = {
        project = "CFDEV",
        -- sprint = "current", -- TODO
      }
    },
  },
  plan = {
    order = 2,
    prompt = "",
    max_iterations = 10,
    max_tokens = 1000,
    temperature = 0.5,
    top_p = 1,
    n = 1,
    stop = "<|endoftext|>",
    logprobs = 10,
    presence_penalty = 0,
    frequency_penalty = 0,
    best_of = 1,
    logit_bias = {},
    user = "**",
  },
}
