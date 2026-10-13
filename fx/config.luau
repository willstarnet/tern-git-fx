--!strict
-- config.json schema: defaults, validation with per-field fallback, and the starter file. Pure.

local classify = require("./classify")

export type Corner = "top-right" | "top-left" | "bottom-right" | "bottom-left"

export type Config = {
	-- Pane corner the animation sits in.
	position: Corner,
	-- Gap from the corner's two edges, CSS px.
	offset_px: number,
	-- Integer upscale of the 32 px sprites.
	scale: number,
	-- A command must run this long before its loop shows; faster ones only play the ending.
	loop_delay_ms: number,
	-- How long the ending's last frame stays up.
	hold_ms: number,
	-- Per-command switch; every command defaults to on.
	commands: { [string]: boolean },
	-- Effective alias tables: built-ins overlaid with the file's `aliases` and `git_aliases`.
	aliases: classify.Aliases,
}

local CORNERS: { [string]: boolean } = {
	["top-right"] = true,
	["top-left"] = true,
	["bottom-right"] = true,
	["bottom-left"] = true,
}

local NUMBERS: { [string]: { min: number, max: number, integer: boolean } } = {
	offset_px = { min = 0, max = 400, integer = false },
	scale = { min = 1, max = 8, integer = true },
	loop_delay_ms = { min = 0, max = 10000, integer = true },
	hold_ms = { min = 0, max = 10000, integer = true },
}

local KEYS = { "position", "offset_px", "scale", "loop_delay_ms", "hold_ms", "commands", "aliases", "git_aliases" }
local KNOWN: { [string]: boolean } = {}
for _, k in KEYS do
	KNOWN[k] = true
end

local function defaults(): Config
	local commands: { [string]: boolean } = {}
	for _, c in classify.COMMANDS do
		commands[c] = true
	end
	return {
		position = "bottom-right",
		offset_px = 20,
		scale = 3,
		loop_delay_ms = 300,
		hold_ms = 900,
		commands = commands,
		aliases = classify.defaultAliases(),
	}
end

-- Overlays a user alias table onto `into`; values must be command names or false.
local function overlayAliases(raw: any, into: classify.AliasMap, key: string, warnings: { string })
	if raw == nil then
		return
	end
	if type(raw) ~= "table" then
		table.insert(warnings, `{key}: expected an object of name -> command`)
		return
	end
	for name, value in raw do
		if type(name) ~= "string" or name == "" or string.find(name, "%s") then
			table.insert(warnings, `{key}: ignored invalid alias name {tostring(name)}`)
		elseif value == false then
			into[name] = false
		elseif classify.isCommand(value) then
			into[name] = value
		else
			table.insert(warnings, `{key}.{name}: {tostring(value)} is not one of the supported git commands`)
		end
	end
end

-- The effective config for the decoded `raw` file content (nil when there is no file), and a
-- warning per field that was ignored. Invalid fields fall back to their defaults one by one.
local function resolve(raw: any): (Config, { string })
	local cfg = defaults()
	local warnings: { string } = {}
	if raw == nil then
		return cfg, warnings
	end
	if type(raw) ~= "table" then
		table.insert(warnings, "config.json: expected an object; using defaults")
		return cfg, warnings
	end

	for k in raw do
		if type(k) ~= "string" or not KNOWN[k] then
			table.insert(warnings, `unknown key {tostring(k)}`)
		end
	end

	if raw.position ~= nil then
		if type(raw.position) == "string" and CORNERS[raw.position] then
			cfg.position = raw.position :: Corner
		else
			table.insert(warnings, `position: expected one of top-right, top-left, bottom-right, bottom-left`)
		end
	end

	for key, rule in NUMBERS do
		local v = raw[key]
		if v == nil then
			continue
		end
		if type(v) ~= "number" or v ~= v or v < rule.min or v > rule.max or (rule.integer and v ~= math.floor(v)) then
			local kind = if rule.integer then "an integer" else "a number"
			table.insert(warnings, `{key}: expected {kind} from {rule.min} to {rule.max}`)
		else
			(cfg :: any)[key] = v
		end
	end

	if raw.commands ~= nil then
		if type(raw.commands) ~= "table" then
			table.insert(warnings, "commands: expected an object of command -> true/false")
		else
			for name, on in raw.commands do
				if not classify.isCommand(name) then
					table.insert(warnings, `commands: unknown command {tostring(name)}`)
				elseif type(on) ~= "boolean" then
					table.insert(warnings, `commands.{name}: expected true or false`)
				else
					cfg.commands[name] = on
				end
			end
		end
	end

	overlayAliases(raw.aliases, cfg.aliases.shell, "aliases", warnings)
	overlayAliases(raw.git_aliases, cfg.aliases.git, "git_aliases", warnings)
	return cfg, warnings
end

-- The starter config.json text: every default spelled out in a fixed order, aliases empty.
local function starterText(): string
	local d = defaults()
	local commands = {}
	for _, c in classify.COMMANDS do
		table.insert(commands, `    "{c}": true`)
	end
	return table.concat({
		"{",
		`  "position": "{d.position}",`,
		`  "offset_px": {d.offset_px},`,
		`  "scale": {d.scale},`,
		`  "loop_delay_ms": {d.loop_delay_ms},`,
		`  "hold_ms": {d.hold_ms},`,
		'  "commands": {',
		table.concat(commands, ",\n"),
		"  },",
		'  "aliases": {},',
		'  "git_aliases": {}',
		"}",
		"",
	}, "\n")
end

return {
	defaults = defaults,
	resolve = resolve,
	starterText = starterText,
}
