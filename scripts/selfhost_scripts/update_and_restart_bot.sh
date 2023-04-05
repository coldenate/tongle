#!/bin/bash

# Set the repository URL and the project directory
REPO_URL="https://github.com/yourusername/yourrepo.git"
PROJECT_DIR="$HOME/code_projects/tongle"

# Update the code from the repository
cd $PROJECT_DIR
git fetch --tags
LATEST_TAG=$(git describe --tags `git rev-list --tags --max-count=1`)
CURRENT_TAG=$(git describe --tags)

if [ "$LATEST_TAG" != "$CURRENT_TAG" ]; then
    git checkout $LATEST_TAG

    # Restart the systemd service
    sudo systemctl restart tongle-bot.service
fi

