#!/bin/bash
set -e  # Exit on any error

## setup dependencies for getting the data

pip3 install datasets

# Expected environment variables
# GITHUB_REPO: URL of the repository
# COMMIT_HASH: Specific commit to checkout

if [ -z "$GITHUB_REPO" ] || [ -z "$COMMIT_HASH" ]; then
    echo "Error: GITHUB_REPO and COMMIT_HASH must be set"
    exit 1
fi

echo "Cloning repository: $GITHUB_REPO"
git clone $GITHUB_REPO repo
cd repo

echo "Checking out commit: $COMMIT_HASH"
git checkout $COMMIT_HASH

# Run tests (modify this based on your project's test command)
echo "Running tests..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi
python3 -m pytest

echo "Build completed successfully!"
