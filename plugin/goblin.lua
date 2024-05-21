vim.api.nvim_create_user_command("GoblinRun", function()
  require("goblin").openWorkflow()
end, {})

vim.api.nvim_create_user_command("GoblinContinue", function()
  require("goblin").continueWorkflow()
end, {})

vim.api.nvim_create_user_command("GoblinTrain", function()
  require("goblin").train()
end, {})
