local goblin = require("goblin")

---@class GoblinSubcommand
---@field impl fun(args:string[], opts: table) The command implementation
---@field complete? fun(subcmd_arg_lead: string): string[] (optional) Command completions callback, taking the lead of the subcommand's arguments
---@type table<string, GoblinSubcommand>
local subcommand_tbl = {
  run = {
    impl = function(args, opts)
      -- Implementation (args is a list of strings)
      goblin.openWorkflow()
    end,
    -- This subcommand has no completions
  },
  train = {
    impl = function(args, opts)
      -- Implementation
      goblin.train()
    end,
  },
}

---@param opts table :h lua-guide-commands-create
local function goblin_run(opts)
  local fargs = opts.fargs
  local subcommand_key = fargs[1]
  -- Get the subcommand's arguments, if any
  local args = #fargs > 1 and vim.list_slice(fargs, 2, #fargs) or {}
  local subcommand = subcommand_tbl[subcommand_key]
  if not subcommand then
    vim.notify("Goblin: Unknown command: " .. subcommand_key, vim.log.levels.ERROR)
    return
  end
  -- Invoke the subcommand
  subcommand.impl(args, opts)
end


vim.api.nvim_create_user_command("Goblin", goblin_run, {
  nargs = "+",
  desc =
  "Goblin is a plugin that allows you to create custom workflows with a focus on automating the process of updating codebases.",
  complete = function(arg_lead, cmdline, _)
    -- Get the subcommand.
    local subcmd_key, subcmd_arg_lead = cmdline:match("^Rocks[!]*%s(%S+)%s(.*)$")
    if subcmd_key and subcmd_arg_lead and subcommand_tbl[subcmd_key] and subcommand_tbl[subcmd_key].complete then
      -- The subcommand has completions. Return them.
      return subcommand_tbl[subcmd_key].complete(subcmd_arg_lead)
    end
    -- Check if cmdline is a subcommand
    if cmdline:match("^Rocks[!]*%s+%w*$") then
      -- Filter subcommands that match
      local subcommand_keys = vim.tbl_keys(subcommand_tbl)
      return vim.iter(subcommand_keys)
          :filter(function(key)
            return key:find(arg_lead) ~= nil
          end)
          :totable()
    end
  end,
  bang = true, -- If you want to support ! modifiers
})
