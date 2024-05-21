local config = {
  data = {
    order = 1,
    source = "jira",
    source_options = {
      domain = "cityflavor.atlassian.net",
      user = "weston@cityflavor.com",
      token =
      "ATATT3xFfGF00IF0a4ntKc-lDfYFgIiu-iX_YTuQ1FPdgDbBo8JSQmU_Hi6lbyBh4rXTNr_gvyIQ5N5JMt-Rb_TeRgjErUq5AImKuCsWxaU7b_W18JjvZLwC_2f8XVMPfwms6mUU0wUXZX-u63OWDpElvEaa0nMmRrrh7wEOpy-MLZAljm-VNLE=4EFBE7B0",
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
    user = "wstewarttennes",
  },
}
