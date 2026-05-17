#!/bin/sh
set -e

# Replace the placeholder in app.js with the actual API_BASE environment variable
# If BACKEND_URL is not set, default to http://localhost:8000
: "${BACKEND_URL:=http://localhost:8000}"

echo "Injecting BACKEND_URL: $BACKEND_URL into app.js"

# Use sed to replace the placeholder
sed -i "s|WINDOW_API_BASE|$BACKEND_URL|g" /usr/share/nginx/html/app.js

# Execute the original CMD
exec "$@"
