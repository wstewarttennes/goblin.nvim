-- module represents a lua module for the plugin
local M = {}

local GoblinWorkFlow = require("goblin.workflow")
local GoblinTrainer = require("goblin.trainer")

M.start = GoblinWorkFlow.start
M.start_workflow = GoblinWorkFlow.start_workflow
M.continue_workflow = GoblinWorkFlow.continue_workflow
M.train = GoblinTrainer.train

return M
