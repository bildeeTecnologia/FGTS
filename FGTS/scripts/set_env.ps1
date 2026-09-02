# Usage: . .\scripts\set_env.ps1
# Sets required environment variables for local runs

$env:SUPABASE_URL = "https://supabase.bildee.com.br"
$env:SUPABASE_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc2NjA2MjMyMCwiZXhwIjo0OTIxNzM1OTIwLCJyb2xlIjoiYW5vbiJ9.0kKgj8siWkfT18wWZHzSGVIJpr7grXnVcDBXnilV12s"

Write-Host "SUPABASE_URL and SUPABASE_KEY set in current session."