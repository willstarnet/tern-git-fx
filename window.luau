--!strict
-- Window half: feeds this window's command and focus events to the player (fx/player.luau),
-- and adds the palette commands. All state is per window and rebuilt at load (window_start
-- does not fire again after a plugin reload).

local config = require("./fx/config")
local player = require("./fx/player")
local sprites = require("./fx/sprites")

local TITLE = "Git FX"
local SHEET = "fx"
local TOGGLE_ID = "toggle"
local TOGGLE_ACTION = `plugin.{tern.plugin.id}.{TOGGLE_ID}`
-- Rebind with a settings.json "keybinds" entry for the action above.
local TOGGLE_CHORD = "ctrl+alt+cmd+g"
local PAUSED_KEY = "paused"
-- config.json is re-read at most this often, when a command starts.
local CONFIG_TTL_MS = 2000
local MAX_CONFIG_BYTES = 256 * 1024

local configPath = tern.plugin.data .. "/config.json"
local cachedConfig: config.Config = config.defaults()
local cachedText: string? = nil
local cachedAt = -math.huge
-- Config problems found since the last event that could show a toast.
local pendingWarnings: { string } = {}
local keysChecked = false

local function readConfig(): config.Config
	local now = tern.now()
	if now - cachedAt < CONFIG_TTL_MS then
		return cachedConfig
	end
	cachedAt = now
	local text: string? = nil
	local exists, present = pcall(tern.fs.exists, configPath)
	if exists and present then
		local ok, result = pcall(tern.fs.read, configPath, MAX_CONFIG_BYTES)
		if ok then
			text = result
		else
			table.insert(pendingWarnings, "config.json is unreadable; using defaults")
		end
	end
	if text == cachedText then
		return cachedConfig
	end
	cachedText = text
	local raw: any = nil
	if text then
		local ok, decoded = pcall(tern.json.decode, text)
		if ok then
			raw = decoded
		else
			table.insert(pendingWarnings, "config.json is not valid JSON; using defaults")
		end
	end
	local cfg, warnings = config.resolve(raw)
	for _, w in warnings do
		table.insert(pendingWarnings, w)
	end
	cachedConfig = cfg
	return cfg
end

local function flushWarnings(cx: WindowCx)
	if #pendingWarnings == 0 then
		return
	end
	for _, w in pendingWarnings do
		tern.log.warn(`tern-git-fx: config.json: {w}`)
	end
	local first = pendingWarnings[1]
	local more = if #pendingWarnings > 1 then ` (+{#pendingWarnings - 1} more in the log)` else ""
	table.clear(pendingWarnings)
	pcall(function()
		cx:toast("error", "Check Git FX config", first .. more)
	end)
end

local function isPaused(): boolean
	local ok, v = pcall(tern.kv.get, PAUSED_KEY)
	return ok and v == true
end

local function focusedPane(cx: WindowCx?): number?
	if cx == nil then
		return nil
	end
	local ok, pane = pcall(function()
		return cx.session:focused()
	end)
	return if ok then pane else nil
end

local function checkChord(cx: WindowCx)
	keysChecked = true
	local ok, keys = pcall(function()
		return cx.actions:keys()
	end)
	if not ok or type(keys) ~= "table" then
		return
	end
	local bound = keys[TOGGLE_CHORD]
	if type(bound) ~= "table" or table.find(bound, TOGGLE_ACTION) == nil then
		tern.log.warn(`tern-git-fx: {TOGGLE_CHORD} is not bound to {TOGGLE_ACTION}; use the palette or rebind it`)
	end
end

local store = sprites.new({
	read = function(path: string, maxBytes: number): string
		return tern.fs.read(path, maxBytes)
	end,
	decode = tern.json.decode,
	base64 = function(bytes: string): string
		return tern.base64.encode(bytes)
	end,
})

local fx = player.new({
	css = function(source: string)
		tern.css(SHEET, source)
	end,
	timer = function(ms: number, fn: (focused: number?) -> ()): () -> ()
		local handle = tern.timer(ms, function(cx: WindowCx?)
			fn(focusedPane(cx))
		end)
		return function()
			handle:cancel()
		end
	end,
	config = readConfig,
	paused = isPaused,
	sprite = function(command, phase)
		return sprites.get(store, command, phase)
	end,
	log = function(level: "debug" | "warn", message: string)
		tern.log[level](message)
	end,
})

local function num(v: any): number?
	return if type(v) == "number" and v == v then v else nil
end

-- Runs a player call for an event, never letting an error escape into Tern (a raising window
-- hook counts against the plugin) and surfacing config problems.
local function handle(name: string, cx: WindowCx, fn: (focused: number?) -> ())
	local ok, err = pcall(fn :: any, focusedPane(cx))
	if not ok then
		tern.log.warn(`tern-git-fx: {name} failed: {err}`)
	end
	if not keysChecked then
		checkChord(cx)
	end
	flushWarnings(cx)
end

tern.on("command_started", function(ev: CommandStartedEvent, cx: WindowCx)
	handle("command_started", cx, function(focused: number?)
		local pane = num(ev.pane)
		if pane then
			player.started(fx, pane, ev.line, focused)
		end
	end)
end)

tern.on("command_finished", function(ev: CommandFinishedEvent, cx: WindowCx)
	handle("command_finished", cx, function(focused: number?)
		local pane = num(ev.pane)
		if pane then
			player.finished(fx, pane, ev.line, num(ev.status), focused)
		end
	end)
end)

tern.on("pane_closed", function(ev: PaneEvent, cx: WindowCx)
	handle("pane_closed", cx, function(focused: number?)
		local pane = num(ev.pane)
		if pane then
			player.closed(fx, pane, focused)
		end
	end)
end)

for _, name in { "focus", "pane_created", "tab_created", "tab_closed" } do
	tern.on(name, function(_ev: any, cx: WindowCx)
		handle(name, cx, function(focused: number?)
			player.focus(fx, focused)
		end)
	end)
end

tern.command({
	id = TOGGLE_ID,
	title = "Toggle git animations",
	group = TITLE,
	keys = { TOGGLE_CHORD },
	run = function(cx: WindowCx)
		local paused = not isPaused()
		local ok, err = pcall(tern.kv.set :: any, PAUSED_KEY, paused)
		if not ok then
			tern.log.warn(`tern-git-fx: saving the toggle failed: {err}`)
			cx:toast("error", "Toggle failed", tostring(err))
			return
		end
		if paused then
			player.clear(fx)
		end
		cx:toast("info", if paused then "Git animations off" else "Git animations on")
	end,
})

tern.command({
	id = "open-config",
	title = "Open git animations config",
	group = TITLE,
	run = function(cx: WindowCx)
		local ok, err = pcall(function()
			if not tern.fs.exists(configPath) then
				tern.fs.mkdir(tern.plugin.data)
				tern.fs.write(configPath, config.starterText())
			end
		end)
		if not ok then
			tern.log.warn(`tern-git-fx: creating config.json failed: {err}`)
			cx:toast("error", "Config not created", tostring(err))
			return
		end
		cx:open(configPath)
	end,
})

-- Installed at load so a reload replaces any sheet the previous VM left behind.
tern.css(SHEET, "/* tern-git-fx: idle */\n")
