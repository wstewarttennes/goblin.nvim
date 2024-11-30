#!/bin/sh

tmux source ~/.tmux.conf
cd ~/dev/goblin.nvim/goblin
tmux new-session -d -s goblin -n goblinWindow 

tmux split-window -h
tmux split-window -v
tmux select-pane -t goblin:goblinWindow.1
tmux split-window -h

tmux send-keys -t goblin:goblinWindow.0 "source venv/bin/activate" Enter
tmux send-keys -t goblin:goblinWindow.0 "pip install -r requirements.txt" Enter
tmux send-keys -t goblin:goblinWindow.0 "vim" Enter

tmux select-pane -t goblin:goblinWindow.0
tmux resize-pane -R 
tmux select-pane -t goblin:goblinWindow.2

tmux send-keys -t goblin:goblinWindow.1 "cd goblin" Enter
tmux send-keys -t goblin:goblinWindow.1 "source venv/bin/activate" Enter
tmux send-keys -t goblin:goblinWindow.1 "goblin up --build" Enter

tmux send-keys -t goblin:goblinWindow.3 "source goblin/venv/bin/activate" Enter
tmux send-keys -t goblin:goblinWindow.3 'export OPENAI_API_KEY=$(op read "op://Coding/openai-api-key/credential")' Enter
tmux send-keys -t goblin:goblinWindow.3 'export TAVILY_API_KEY=$(op read "op://Coding/tavily-api-key/credential")' Enter

tmux send-keys -t goblin:goblinWindow.2 "cd apps/desktop" Enter
tmux send-keys -t goblin:goblinWindow.2 "npm install" Enter
tmux send-keys -t goblin:goblinWindow.2 'export OPENAI_API_KEY=$(op read "op://Coding/openai-api-key/credential")' Enter
tmux send-keys -t goblin:goblinWindow.2 'export TAVILY_API_KEY=$(op read "op://Coding/tavily-api-key/credential")' Enter
tmux send-keys -t goblin:goblinWindow.2 "npm run start" Enter

tmux select-pane -t goblin:goblinWindow.0
tmux attach -t goblin:goblinWindow
