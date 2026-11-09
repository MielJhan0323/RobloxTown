# Connect Claude to Roblox Studio on an M1 Mac (files stored in the cloud)

Laptop: Roblox Studio + Claude Code (+ Studio MCP) + OBS. Recordings go straight to Google Drive.
Cloud session: downloads the clips, does voice / captions / music / render, sends back the video.

## 1. Roblox Studio (~10 min)
1. Download Studio from https://create.roblox.com → drag to Applications → open → sign in.
2. New → **Baseplate**. Keep this window open whenever Claude works.

## 2. Claude Code (~5 min)
1. Open **Terminal** (Cmd+Space → "Terminal").
2. Run the installer shown on https://code.claude.com (at the time of writing):
   `curl -fsSL https://claude.ai/install.sh | bash`
3. Quit Terminal (Cmd+Q), reopen it, run `claude`, log in with your Claude account, then type `/exit`.

## 3. Roblox Studio MCP (lets Claude build/pose/animate inside Studio) (~10 min)
1. Open https://github.com/Roblox/studio-rust-mcp-server → **Releases** → download the **macOS** file.
2. Unzip, open it. If macOS blocks it: System Settings → Privacy & Security → **Open Anyway**.
   It installs a plugin into Roblox Studio.
3. Register it with Claude Code using the command in the README's **Claude Code** section
   (it's a `claude mcp add ...` line pointing at the app you just installed).
4. Check: `claude mcp list` → Roblox Studio should be listed as connected.
5. Quit and reopen Roblox Studio → **Plugins** tab → make sure the MCP plugin is on.
   If it says it can't connect: Home → Game Settings → Security → turn on **Allow HTTP Requests**, then retry.

## 4. Google Drive (cloud storage, keeps the laptop light) (~5 min)
1. Install **Google Drive for desktop** → sign in → Preferences (gear) → Google Drive → **Stream files**.
2. In Finder → Google Drive → My Drive → make folders `RobloxTown/raw/lighthouse`.
3. On drive.google.com: right-click `RobloxTown` → Share → General access: **Anyone with the link → Viewer** → Copy link.
   Send that link to Claude once.

## 5. OBS (recording) (~10 min)
1. Install OBS from https://obsproject.com (Apple Silicon build) → open → skip the wizard.
2. System Settings → Privacy & Security → **Screen & System Audio Recording** → allow OBS → reopen OBS.
3. OBS Settings → **Video**: Base and Output resolution `1080x1920`, FPS 30.
4. OBS Settings → **Output** → Recording: Path = the Drive folder `My Drive/RobloxTown/raw/lighthouse`, Format = **MP4**.
5. Sources → **+** → macOS Screen Capture → Method: Window → **Roblox Studio** → fit to screen (Cmd+F).
6. Tools → **WebSocket Server Settings** → Enable → Show Connect Info → note the password
   (lets Claude start/stop recordings by itself).

## 6. The project + test (~5 min)
```
git clone -b claude/clever-maxwell-t5glbr https://github.com/MielJhan0323/RobloxTown.git
cd RobloxTown
claude
```
(If the Mac asks to install developer tools for `git`, click Install, then run the line again.)

Test: *"What's in my Roblox Studio workspace?"* → it should mention the Baseplate. Connected.

## 7. Drive it from your phone (optional)
In the `RobloxTown` folder run `claude remote-control` instead of `claude`; the session appears in the
Claude app. Keep the Mac awake (System Settings → Lock Screen / Battery: prevent sleep while plugged in),
with Studio and OBS open.

## Then
Say: *"Build and record the lighthouse shots in Studio from scripts/lighthouse.md"*. Clips land in Drive;
tell the cloud session "clips are up" (with the folder link) for the edit.
