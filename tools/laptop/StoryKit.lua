--[[
StoryKit - small helpers for recording "In This Town" shots in Roblox Studio.
Put this in ReplicatedStorage as a ModuleScript named "StoryKit" (laptop Claude: create it via MCP).
Use from the command bar / MCP run_code:
    local K = require(game.ReplicatedStorage.StoryKit)
    K.setFace(workspace.Lily, "smile")
    K.setMeter(workspace.Lily, "1 DAY")
    K.faceSequence(workspace.Narrator, {{0, "neutral"}, {0.8, "shocked"}})
    K.countMeter(workspace.Lily, 0, 30, 1.2, " YEARS")
    K.lockCamera(workspace.Cams.Shot42)   -- a Part placed where the camera should be

Faces: the reference videos use CLASSIC flat face decals (not Dynamic Heads). Give every character a
classic head, then fill FACES below once with decal ids found in the Toolbox / Creator Store
(search the terms in the comments). Keep the same ids for the whole series.
NOTE: written without access to Studio - if something errors, fix it in place.
]]

local StoryKit = {}

StoryKit.FACES = {
	neutral     = "", -- search: "classic face neutral" / "Smile" (plain)
	smile       = "", -- "smile face"
	grin        = "", -- "big grin face"
	laugh       = "", -- "laughing face closed eyes"
	talk        = "", -- "open mouth face" (use while a character speaks)
	shocked     = "", -- "shocked face O mouth"
	sad         = "", -- "sad face frown"
	crying      = "", -- "crying face tears"
	worried     = "", -- "worried face"
	tired       = "", -- "tired face" / "sleepy face droopy eyes"
	sleeping    = "", -- "sleeping face closed eyes"
	determined  = "", -- "determined face"
	embarrassed = "", -- "blush face"
	smirk       = "", -- "smirk face"
	angry       = "", -- "angry face"
}

local function head(char)
	return char and char:FindFirstChild("Head")
end

function StoryKit.setFace(char, name)
	local h = head(char)
	if not h then warn("StoryKit.setFace: no Head in", char) return end
	local face = h:FindFirstChild("face") or h:FindFirstChildOfClass("Decal")
	if not face then
		face = Instance.new("Decal")
		face.Name = "face"
		face.Face = Enum.NormalId.Front
		face.Parent = h
	end
	local id = StoryKit.FACES[name]
	if id == nil or id == "" then
		warn("StoryKit.setFace: no decal id for face '" .. tostring(name) .. "' - fill StoryKit.FACES")
		return
	end
	if tonumber(id) then id = "rbxassetid://" .. id end
	face.Texture = id
end

-- steps = {{seconds, "faceName"}, ...}; runs in the background so you can start recording first
function StoryKit.faceSequence(char, steps)
	for _, step in ipairs(steps) do
		task.delay(step[1], function()
			StoryKit.setFace(char, step[2])
		end)
	end
end

local function arm(char)
	return char:FindFirstChild("LeftLowerArm") or char:FindFirstChild("Left Arm")
end

-- Glowing wrist meter (same look in every shot). hidden=true puts it "under the bracelet".
function StoryKit.setMeter(char, text, hidden)
	local a = arm(char)
	if not a then warn("StoryKit.setMeter: no left arm in", char) return end
	local m = a:FindFirstChild("WristMeter")
	if not m then
		m = Instance.new("Part")
		m.Name = "WristMeter"
		m.Size = Vector3.new(0.55, 0.35, 0.08)
		m.Color = Color3.fromRGB(25, 25, 30)
		m.Material = Enum.Material.SmoothPlastic
		m.CanCollide = false
		m.Massless = true
		m.CFrame = a.CFrame * CFrame.new(0, -a.Size.Y / 2 + 0.3, -a.Size.Z / 2 - 0.04)
		local weld = Instance.new("WeldConstraint")
		weld.Part0 = a
		weld.Part1 = m
		weld.Parent = m
		local gui = Instance.new("SurfaceGui")
		gui.Name = "Screen"
		gui.Face = Enum.NormalId.Front
		gui.LightInfluence = 0
		gui.Brightness = 2
		gui.PixelsPerStud = 200
		gui.Parent = m
		local label = Instance.new("TextLabel")
		label.Name = "Readout"
		label.Size = UDim2.fromScale(1, 1)
		label.BackgroundTransparency = 1
		label.TextScaled = true
		label.Font = Enum.Font.GothamBold
		label.TextColor3 = Color3.fromRGB(90, 255, 210)
		label.Parent = gui
		local glow = Instance.new("PointLight")
		glow.Color = Color3.fromRGB(90, 255, 210)
		glow.Range = 3
		glow.Brightness = 1.5
		glow.Parent = m
		m.Parent = a
	end
	m.Screen.Readout.Text = text or ""
	m.Transparency = hidden and 1 or 0
	m.Screen.Enabled = not hidden
	m.PointLight.Enabled = not hidden
end

-- Animate the number (e.g. 0 -> 30 YEARS) for the "numbers flickered" shots.
function StoryKit.countMeter(char, from, to, seconds, suffix)
	suffix = suffix or ""
	task.spawn(function()
		local steps = math.max(1, math.floor(seconds * 20))
		for i = 0, steps do
			local v = from + (to - from) * (i / steps)
			StoryKit.setMeter(char, tostring(math.floor(v + 0.5)) .. suffix)
			task.wait(seconds / steps)
		end
	end)
end

-- Put the editor camera exactly where a marker Part is (make one Part per shot, e.g. workspace.Cams.Shot42).
function StoryKit.lockCamera(marker, fov)
	local cam = workspace.CurrentCamera
	cam.CameraType = Enum.CameraType.Scriptable
	cam.CFrame = marker.CFrame
	if fov then cam.FieldOfView = fov end
end

return StoryKit
