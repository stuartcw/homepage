#!/bin/bash

#!/bin/bash

# Script to copy Jekyll theme files from `jekyll-theme-minimal` to the local Jekyll project
# Usage: Run this script from the root of your Jekyll project

# Function to print error message and exit
error_exit() {
  echo "[ERROR] $1"
  exit 1
}

# Locate the Ruby gems directory
echo "Locating Ruby gems directory..."
GEMS_DIR=$(gem env gemdir 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$GEMS_DIR" ]; then
  error_exit "Could not locate Ruby gems directory. Ensure Ruby and Rubygems are properly installed."
fi

THEME_PATH="$GEMS_DIR/gems/jekyll-theme-minimal-"
THEME_DIR=$(ls -d ${THEME_PATH}* 2>/dev/null | head -n 1)

if [ -z "$THEME_DIR" ]; then
  error_exit "Could not locate the jekyll-theme-minimal files. Ensure the theme is installed with 'gem install jekyll-theme-minimal'."
fi

echo "Found theme path: $THEME_DIR"

# Directories to copy from the theme
DIRECTORIES=("_layouts" "_includes" "_sass" "assets")

# Copy files to the local project
for dir in "${DIRECTORIES[@]}"; do
  if [ -d "$THEME_DIR/$dir" ]; then
    echo "Copying $dir to the project root..."
    mkdir -p "./$dir" || error_exit "Failed to create directory ./$dir"
    cp -r "$THEME_DIR/$dir/"* "./$dir/" || error_exit "Failed to copy $dir"
  else
    echo "[INFO] Directory $dir does not exist in the theme, skipping."
  fi
done

echo "All files copied successfully."

# Instructions to the user
cat <<EOF

[INFO] The theme files have been copied to your project. You can now modify them as needed.
Make sure to test your changes by running:
  jekyll serve
EOF

exit 0
