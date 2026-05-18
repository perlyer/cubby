# cubby demo — render with:  vhs assets/demo.tape   (run from the repo root)
# Produces assets/demo.gif

Output assets/demo.gif

Set Shell "bash"
Set FontSize 18
Set Width 1100
Set Height 940
Set Padding 24
Set TypingSpeed 55ms
Set CursorBlink false

# --- off-camera setup: an isolated, throwaway store ---
Hide
Type `export PATH="$PWD:$PATH" CUBBY_HOME="$(mktemp -d)/cubby"`
Enter
Sleep 500ms
Type "cubby init >/dev/null && clear"
Enter
Sleep 3s
Show

# 1. what cubby is — the banner + command catalogue
Type "cubby"
Sleep 600ms
Enter
Sleep 3s

# clear the catalogue off-camera so the next beats start fresh
Hide
Type "clear"
Enter
Sleep 300ms
Show

# 2. store a secret — the value is typed at a hidden prompt
Type "cubby set db-password"
Sleep 500ms
Enter
Sleep 900ms
Type "hunter2"
Sleep 500ms
Enter
Sleep 1.6s

# 3. inspect it — metadata only, the value is never shown
Type "cubby get db-password"
Sleep 500ms
Enter
Sleep 3s

# 4. use it — cubby injects the secret into the command's environment
Type "cubby run -- sh -c 'echo connected with $DB_PASSWORD'"
Sleep 500ms
Enter
Sleep 3s

Sleep 1.2s
