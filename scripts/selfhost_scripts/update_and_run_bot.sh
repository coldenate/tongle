#!/bin/bash

# Set the repository URL and the project directory
REPO_URL="https://github.com/yourusername/yourrepo.git"
PROJECT_DIR="$HOME/code_projects/tongle"

# Update the code from the repository
cd $PROJECT_DIR
git fetch --tags
LATEST_TAG=$(git describe --tags `git rev-list --tags --max-count=1`)
git checkout $LATEST_TAG

# Load the environment variables from the .prod.env file
export $(grep -v '^#' src/.prod.env | xargs)

# Run the bot using Nix shell
/home/n8sol/.nix-profile/bin/nix-shell --run run_bot
