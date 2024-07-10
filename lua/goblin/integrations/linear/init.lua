local curl = require("plenary.curl")
local Utils = require("goblin.integrations.linear.utils")
local json = require("packages.dkjson.dkjson")

---@class LinearConfig
local config = {
  domain = vim.env.LINEAR_DOMAIN,
  user = vim.env.LINEAR_USER,
  token = vim.env.LINEAR_API_TOKEN,
  key = vim.env.LINEAR_PROJECT_KEY or "PM",
}

---@param issue_id string
local function get_issue(issue_id)
  local response = curl.post("https://api.linear.app/graphql", {
    headers = {
      ["Content-Type"] = "application/json",
      ["Authorization"] = config.token,
    },
    body = [[
      { "query": "{ issue(id: ) { nodes { id title } } }" }
    ]]
  })
  print(response)
  if response.status < 400 then
    return vim.fn.json_decode(response.body)
  else
    print("Non 200 response: " .. response.status)
  end
end

local Linear = {}

function Linear.open_issue()
  -- local issue_id = Linear.parse_issue() or vim.fn.input("Issue: ")
  -- local url = "https://" .. config.domain .. "/browse/" .. issue_id
  -- local os_name = vim.loop.os_uname().sysname
  -- local is_windows = vim.loop.os_uname().version:match("Windows")
  --
  -- if os_name == "Darwin" then
  --   os.execute("open " .. url)
  -- elseif os_name == "Linux" then
  --   os.execute("xdg-open " .. url)
  -- elseif is_windows then
  --   os.execute("start " .. url)
  -- end
end

function Linear.get_issues(params)
  local body
  print(params.label)
  if params.label then
    body = [[
      {
        issues(filter: {labels: {name: {eq: "]] .. params.label .. [["}}}) {
          nodes {
            id
            title
            description
            labels {
              nodes {
                name
              }
            }
          }
        }
      }
    ]]
    body = json.encode({
      query = body,
      variables = {
        labelName = params.label
      }
    })
  else
    body = [[
      { "query": "{ issues { nodes { id title } } }" }
    ]]
  end

  local response = curl.post("https://api.linear.app/graphql", {
    headers = {
      ["Content-Type"] = "application/json",
      ["Authorization"] = config.token,
    },
    body = body
  })
  if response.status < 400 then
    return vim.fn.json_decode(response.body)
  else
    print("Non 200 response: " .. response.status)
  end
end

function Linear.view_issue()
  -- local issue_id = Linear.parse_issue() or vim.fn.input("Issue: ")
  -- local issue = get_issue(issue_id)
  -- vim.schedule(function()
  --   if issue == nil then
  --     print("Invalid response")
  --     return
  --   end
  --   local assignee = ""
  --   if issue.fields.assignee ~= vim.NIL then
  --     local i, j = string.find(issue.fields.assignee.displayName, "%w+")
  --     if i ~= nil then
  --       assignee = " - @" .. string.sub(issue.fields.assignee.displayName, i, j)
  --     end
  --   end
  --   local content = {
  --     issue.fields.summary,
  --     "---",
  --     "`" .. issue.fields.status.name .. "`" .. assignee,
  --     "",
  --     Utils.adf_to_markdown(issue.fields.description),
  --   }
  --   vim.lsp.util.open_floating_preview(content, "markdown", { border = "rounded" })
  -- end)
end

---@return string | nil
function Linear.parse_issue()
  local current_word = vim.fn.expand("<cWORD>")
  local i, j = string.find(current_word, config.key .. "%-%d+")
  if i == nil then
    return nil
  end

  return string.sub(current_word, i, j)
end

---@param opts? LinearConfig
---@return LinearConfig
function Linear.setup(opts)
  opts = opts or {}
  config = vim.tbl_deep_extend("force", config, opts)
  vim.api.nvim_create_user_command("LinearView", Linear.view_issue, {})
  vim.api.nvim_create_user_command("LinearOpen", Linear.open_issue, {})
  return config
end

return Linear
