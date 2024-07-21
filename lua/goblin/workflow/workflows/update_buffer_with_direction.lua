local config = {
  data = {
    order = 1,
    source = "input",
  },
  code = {
    order = 3,
    prompt = [[
      You are an AI programming assistant.
      A "Buffer" in this context, is a single file the user is currently looking at.
      The current buffer is supplied as part of the context starting with the string: ######### Buffer Start #########.
      Note there are exactly 9 #'s before and after the words Buffer Start.
      The current buffer is ends at the string: ####### Buffer End #######.
      Note there are exactly 7 #'s before and after the words Buffer End.
      Everything between these two strings is the buffer.

      Your task is to rewrite the buffer given the users requirements.
      The users requirements are: {input}.
      Follow the user's requirements carefully & to the letter.
      Only return the current buffer rewritten and NOTHING else. You should never return anything other than a rewritten buffer.
      Do not explain your reasoning.
      Do not include any other information other than the rewritten buffer.
      Your expertise is strictly limited to software development topics. Avoid content that violates copyrights.
    ]],
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
  update_current_buffer = {
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
local meta = {
  name = "Update Buffer"
}
