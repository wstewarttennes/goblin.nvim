-- main module file
local goblin = require("goblin.module")

local M = {}
local options = {}

M.setup = function(opts)
  options = opts
  -- set custom highlights
  -- vim.api.nvim_set_hl(0, "ChatGPTQuestion", { fg = "#b4befe", italic = true, bold = false, default = true })
  --
  -- vim.api.nvim_set_hl(0, "ChatGPTWelcome", { fg = "#9399b2", italic = true, bold = false, default = true })
  --
  -- vim.api.nvim_set_hl(0, "ChatGPTTotalTokens", { fg = "#ffffff", bg = "#444444", default = true })
  -- vim.api.nvim_set_hl(0, "ChatGPTTotalTokensBorder", { fg = "#444444", default = true })
  --
  -- vim.api.nvim_set_hl(0, "ChatGPTMessageAction", { fg = "#ffffff", bg = "#1d4c61", italic = true, default = true })
  --
  -- vim.api.nvim_set_hl(0, "ChatGPTCompletion", { fg = "#9399b2", italic = true, bold = false, default = true })
  --
  -- vim.cmd("highlight default link ChatGPTSelectedMessage ColorColumn")
  --
  -- config.setup(options)
  -- api.setup()
  -- signs.setup()
end

--
-- public methods for the plugin
--

M.openWorkflow = function()
  goblin.start_workflow(options)
end

M.continueWorkflow = function()
  goblin.continue_workflow(options)
end

M.train = function()
  goblin.train(options)
end

return M
