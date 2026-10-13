--!strict
-- Per-pane animation state for one window, behind injected ports. Pure apart from the ports.
--
-- A git command moves its pane through: pending (started, loop not shown yet) -> loop (after
-- `loop_delay_ms`) -> success | fail (on finish, by exit status) -> cleared (after the ending's
-- frames plus `hold_ms`). Only the focused pane can be drawn (the overlay selector follows
-- focus), so every transition and focus change re-renders that pane's state. An ending shows only
-- while its pane keeps focus: leaving the pane drops it rather than replaying it on return.

local classify = require("./classify")
local config = require("./config")
local css = require("./css")
local sprites = require("./sprites")

export type Phase = "pending" | "loop" | "success" | "fail"

export type Ports = {
	css: (source: string) -> (),
	-- Calls `fn` once after `ms` with the then-focused pane; returns a cancel function.
	timer: (ms: number, fn: (focused: number?) -> ()) -> () -> (),
	config: () -> config.Config,
	paused: () -> boolean,
	sprite: (command: classify.Command, phase: sprites.Phase) -> (sprites.Sprite?, string?),
	log: (level: "debug" | "warn", message: string) -> (),
}

type PaneState = {
	command: classify.Command,
	phase: Phase,
	-- Unique per shown animation: names its keyframes and identifies the installed sheet.
	seq: number,
	config: config.Config,
	-- An ending may show only while this is true (cleared when focus leaves the pane).
	fresh: boolean,
	cancel: (() -> ())?,
}

export type Player = {
	ports: Ports,
	panes: { [number]: PaneState },
	focused: number?,
	installed: string,
	seq: number,
	reported: { [string]: boolean },
}

-- A loop whose finish never arrives (shell integration lost) is dropped after this long.
local LOOP_MAX_MS = 60 * 60 * 1000
local EMPTY_KEY = "empty"

local function new(ports: Ports): Player
	return { ports = ports, panes = {}, focused = nil, installed = EMPTY_KEY, seq = 0, reported = {} }
end

local function nextSeq(p: Player): number
	p.seq += 1
	return p.seq
end

local function cancel(st: PaneState)
	if st.cancel then
		st.cancel()
		st.cancel = nil
	end
end

local function visible(st: PaneState): boolean
	return st.phase == "loop" or ((st.phase == "success" or st.phase == "fail") and st.fresh)
end

local function sourceFor(p: Player, st: PaneState): string
	local phase: sprites.Phase = st.phase :: any
	local sprite, err = p.ports.sprite(st.command, phase)
	if sprite == nil then
		local key = `{st.command}/{phase}`
		if not p.reported[key] then
			p.reported[key] = true
			p.ports.log("warn", `tern-git-fx: {key} unavailable: {err or "unknown error"}`)
		end
		return css.EMPTY
	end
	local source = css.sheet({
		name = `tern-git-fx-{st.seq}`,
		url = sprite.url,
		frame_w = sprite.frame_w,
		frame_h = sprite.frame_h,
		durations_ms = sprite.durations_ms,
		loop = st.phase == "loop",
		scale = st.config.scale,
		position = st.config.position,
		offset_px = st.config.offset_px,
	})
	return source or css.EMPTY
end

local function render(p: Player)
	local pane = p.focused
	local st = if pane then p.panes[pane] else nil
	local key = EMPTY_KEY
	if pane and st and visible(st) then
		key = `{pane}:{st.seq}`
	end
	if key == p.installed then
		return
	end
	p.installed = key
	if key == EMPTY_KEY then
		p.ports.css(css.EMPTY)
	else
		p.ports.css(sourceFor(p, st :: PaneState))
	end
end

local function setFocus(p: Player, focused: number?)
	if focused == p.focused then
		return
	end
	local left = if p.focused then p.panes[p.focused] else nil
	if left then
		left.fresh = false
	end
	p.focused = focused
end

local function clearIf(p: Player, pane: number, st: PaneState)
	if p.panes[pane] == st then
		cancel(st)
		p.panes[pane] = nil
	end
end

local function toLoop(p: Player, pane: number, st: PaneState)
	st.phase = "loop"
	st.seq = nextSeq(p)
	st.cancel = p.ports.timer(LOOP_MAX_MS, function(focused: number?)
		setFocus(p, focused)
		if p.panes[pane] == st and st.phase == "loop" then
			clearIf(p, pane, st)
			render(p)
		end
	end)
end

local function ending(p: Player, pane: number, st: PaneState, status: number?)
	cancel(st)
	st.phase = if status == 0 then "success" else "fail"
	st.seq = nextSeq(p)
	st.fresh = p.focused == pane
	local total = 0
	local sprite = p.ports.sprite(st.command, st.phase :: any)
	if sprite then
		for _, d in sprite.durations_ms do
			total += d
		end
	end
	st.cancel = p.ports.timer(total + st.config.hold_ms, function(focused: number?)
		setFocus(p, focused)
		clearIf(p, pane, st)
		render(p)
	end)
end

-- The git command `line` runs if it should animate under the current config, and that config.
local function wanted(p: Player, line: any): (classify.Command?, config.Config?)
	if p.ports.paused() then
		return nil, nil
	end
	local cfg = p.ports.config()
	local command = classify.classify(line, cfg.aliases)
	if command == nil or cfg.commands[command] ~= true then
		return nil, nil
	end
	return command, cfg
end

local function started(p: Player, pane: number, line: any, focused: number?)
	setFocus(p, focused)
	local command, cfg = wanted(p, line)
	if command == nil or cfg == nil then
		render(p)
		return
	end
	local old = p.panes[pane]
	if old then
		cancel(old)
	end
	local st: PaneState = { command = command, phase = "pending", seq = nextSeq(p), config = cfg, fresh = true }
	p.panes[pane] = st
	if cfg.loop_delay_ms <= 0 then
		toLoop(p, pane, st)
	else
		st.cancel = p.ports.timer(cfg.loop_delay_ms, function(now: number?)
			setFocus(p, now)
			if p.panes[pane] == st and st.phase == "pending" then
				st.cancel = nil
				toLoop(p, pane, st)
			end
			render(p)
		end)
	end
	render(p)
end

local function finished(p: Player, pane: number, line: any, status: number?, focused: number?)
	setFocus(p, focused)
	local st = p.panes[pane]
	if st and (st.phase == "pending" or st.phase == "loop") then
		ending(p, pane, st, status)
	elseif st == nil then
		-- The start was missed (the plugin reloaded mid-command): play the ending alone.
		local command, cfg = wanted(p, line)
		if command and cfg then
			local fresh: PaneState =
				{ command = command, phase = "pending", seq = nextSeq(p), config = cfg, fresh = true }
			p.panes[pane] = fresh
			ending(p, pane, fresh, status)
		end
	end
	render(p)
end

local function focus(p: Player, focused: number?)
	setFocus(p, focused)
	render(p)
end

local function closed(p: Player, pane: number, focused: number?)
	local st = p.panes[pane]
	if st then
		clearIf(p, pane, st)
	end
	setFocus(p, focused)
	render(p)
end

-- Drops every pane's animation (pausing, or the plugin shutting the overlay off).
local function clear(p: Player)
	for pane, st in p.panes do
		cancel(st)
		p.panes[pane] = nil
	end
	render(p)
end

return {
	LOOP_MAX_MS = LOOP_MAX_MS,
	new = new,
	started = started,
	finished = finished,
	focus = focus,
	closed = closed,
	clear = clear,
}
