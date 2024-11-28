-- lua/goblin/audio/init.lua
local M = {}
local curl = require('plenary.curl')
local Job = require('plenary.job')

-- Configuration
M.config = {
  server_url = "http://localhost:8765",
}

local current_recording = nil
local status_check_timer = nil

-- Function to check transcription status
local function check_transcription_status()
  curl.get(M.config.server_url .. "/status", {
    callback = function(response)
      if response.status == 200 then
        local result = vim.json.decode(response.body)
        if not result.is_recording then
          -- Stop the status check timer if recording has stopped
          if status_check_timer then
            status_check_timer:stop()
            status_check_timer = nil
          end
        end
      end
    end
  })
end

-- Start recording
function M.start_recording()
  if current_recording then
    print("Already recording")
    return
  end

  -- Start recording on the server
  curl.post(M.config.server_url .. "/start", {
    callback = function(response)
      if response.status == 200 then
        current_recording = true
        print("Recording started...")

        -- Update UI to show recording status
        vim.api.nvim_exec([[
                    highlight RecordingStatus guifg=#ff0000 guibg=NONE
                    set statusline+=%#RecordingStatus#\ RECORDING\ %*
                ]], false)

        -- Start status check timer
        if status_check_timer then
          status_check_timer:stop()
        end
        status_check_timer = vim.loop.new_timer()
        status_check_timer:start(1000, 1000, vim.schedule_wrap(check_transcription_status))
      else
        print("Failed to start recording")
      end
    end
  })
end

-- Stop recording
function M.stop_recording()
  if not current_recording then
    print("No recording in progress")
    return
  end

  -- Stop recording on the server
  curl.post(M.config.server_url .. "/stop", {
    callback = function(response)
      if response.status == 200 then
        current_recording = nil
        print("Recording stopped")

        -- Reset statusline
        vim.api.nvim_exec([[
                    set statusline-=%#RecordingStatus#\ RECORDING\ %*
                ]], false)

        -- Stop status check timer
        if status_check_timer then
          status_check_timer:stop()
          status_check_timer = nil
        end
      else
        print("Failed to stop recording")
      end
    end
  })
end

-- Toggle recording
function M.toggle_streaming()
  if current_recording then
    M.stop_recording()
  else
    M.start_recording()
  end
end

-- Setup function
function M.setup(user_config)
  if user_config then
    M.config = vim.tbl_deep_extend('force', M.config, user_config)
  end
end

return M
