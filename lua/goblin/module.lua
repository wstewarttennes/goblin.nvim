-- module represents a lua module for the plugin
local M = {}

local GoblinChat = require("goblin.chat")
local GoblinWorkFlow = require("goblin.workflow")
local GoblinTrainer = require("goblin.trainer")
local GoblinAudio = require("goblin.audio")

M.start = GoblinWorkFlow.start
M.ask = GoblinChat.ask
M.toggle_streaming = GoblinAudio.toggle_streaming
M.start_workflow = GoblinWorkFlow.start_workflow
M.continue_workflow = GoblinWorkFlow.continue_workflow
M.train = GoblinTrainer.train

return M
