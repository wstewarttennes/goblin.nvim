local Popup = require("nui.popup")
local Layout = require("nui.layout")
local Split = require("nui.split")
local event = require("nui.utils.autocmd").event

local data = require("goblin.workflow.steps.data")
local plan = require("goblin.workflow.steps.plan")
local code = require("goblin.workflow.steps.code")
local push = require("goblin.workflow.steps.push")
local aider = require("goblin.workflow.steps.aider")
local replace_buffer = require("goblin.workflow.steps.replace_buffer")
local json = require("packages.dkjson.dkjson")
local audio = require("goblin.audio")

local M = {}

-- Initialize default configuration
M.config = {
  -- Window dimensions and position (in percentage of editor size)
  width = 0.8,  -- 80% of editor width
  height = 0.6, -- 60% of editor height
  border = 'rounded',

  -- Highlight groups
  highlights = {
    border = 'FloatBorder',
    background = 'Normal',
  },
}

local function create_window()
  -- Calculate window size
  local width = math.floor(vim.o.columns * M.config.width)
  local height = math.floor(vim.o.lines * M.config.height)

  -- Calculate window position (centered)
  local row = math.floor((vim.o.lines - height) / 2)
  local col = math.floor((vim.o.columns - width) / 2)

  -- Create a new buffer for the window
  buf_id = vim.api.nvim_create_buf(false, true)

  -- Set buffer options
  vim.api.nvim_buf_set_option(buf_id, 'bufhidden', 'hide')
  vim.api.nvim_buf_set_option(buf_id, 'modifiable', true)
  vim.api.nvim_buf_set_option(buf_id, 'buftype', 'nofile')

  -- Window options
  local opts = {
    relative = 'editor',
    width = width,
    height = height,
    row = row,
    col = col,
    anchor = 'NW',
    style = 'minimal',
    border = M.config.border,
  }

  -- Create the window
  win_id = vim.api.nvim_open_win(buf_id, true, opts)

  -- Set window options
  vim.api.nvim_win_set_option(win_id, 'winblend', 0)
  vim.api.nvim_win_set_option(win_id, 'winhighlight', 'Normal:' .. M.config.highlights.background)

  -- Add window-local keymaps
  vim.api.nvim_buf_set_keymap(buf_id, 'n', 'q', ':lua require("popup").toggle()<CR>', {
    noremap = true,
    silent = true
  })
end

ask = function()
  create_window()
  audio.toggle_streaming()
end

-- Expose module functions
M.ask = ask

return M
