--!strict
-- The overlay sheet: one sprite-strip animation in a corner of the focused pane. Pure.
--
-- The sprite is the `::before` of the focused pane's `div.tv-layer` (Tern's layer over the
-- terminal view), so it leaves the layer's `::after` and the effects layers to other plugins.
-- Panes of hidden tabs and sessions keep `.on` and gain `.off`, hence `:not(.off)`.
-- Each sheet names its keyframes uniquely, so installing a new sheet always restarts the
-- animation from its first frame.

local config = require("./config")

export type Params = {
	-- Keyframes name; sanitized to [a-z0-9-].
	name: string,
	-- data:image/png;base64 URL of a horizontal strip of frames.
	url: string,
	frame_w: number,
	frame_h: number,
	durations_ms: { number },
	-- true: repeat forever; false: play once and hold the last frame.
	loop: boolean,
	scale: number,
	position: config.Corner,
	offset_px: number,
}

local SELECTOR = "section.tn-pane.on:not(.off) > div.tn-body > div.tv > div.tv-layer::before"
local EMPTY = "/* tern-git-fx: idle */\n"
local DATA_PREFIX = "data:image/png;base64,"
local MAX_URL_BYTES = 2 * 1024 * 1024
local Z = 2147483000

local SIDES: { [string]: { v: string, h: string } } = {
	["top-right"] = { v = "top", h = "right" },
	["top-left"] = { v = "top", h = "left" },
	["bottom-right"] = { v = "bottom", h = "right" },
	["bottom-left"] = { v = "bottom", h = "left" },
}

local function num(n: number): string
	if n == math.floor(n) then
		return string.format("%d", n)
	end
	local s = string.format("%.3f", n)
	s = string.gsub(s, "0+$", "")
	s = string.gsub(s, "%.$", "")
	return s
end

local function px(n: number): string
	return num(n) .. "px"
end

local function safeName(v: string): string
	local name = string.sub(string.gsub(string.lower(v), "[^a-z0-9%-]", ""), 1, 64)
	return if name == "" then "tern-git-fx" else name
end

local function safeUrl(v: string): string?
	if #v > MAX_URL_BYTES or string.sub(v, 1, #DATA_PREFIX) ~= DATA_PREFIX then
		return nil
	end
	local payload = string.sub(v, #DATA_PREFIX + 1)
	if #payload == 0 or not string.match(payload, "^[A-Za-z0-9+/]+=*$") then
		return nil
	end
	return v
end

-- One stop per frame at the frame's start, plus 100% on the last frame; with `step-end` timing
-- each frame holds for exactly its own duration.
local function keyframes(name: string, durations: { number }, stepPx: number): string
	local total = 0
	for _, d in durations do
		total += d
	end
	local lines = { `@keyframes {name} \{` }
	local elapsed = 0
	for i, d in durations do
		table.insert(lines, `\t{num(elapsed / total * 100)}% \{ background-position: {px(-(i - 1) * stepPx)} 0px; }`)
		elapsed += d
	end
	table.insert(lines, `\t100% \{ background-position: {px(-(#durations - 1) * stepPx)} 0px; }`)
	table.insert(lines, "}")
	return table.concat(lines, "\n")
end

-- The sheet for `p`, or nil when a parameter is unusable (the caller installs EMPTY instead).
local function sheet(p: Params): string?
	local url = safeUrl(p.url)
	local side = SIDES[p.position]
	local n = #p.durations_ms
	if url == nil or side == nil or n == 0 then
		return nil
	end
	local total = 0
	for _, d in p.durations_ms do
		if type(d) ~= "number" or d <= 0 or d ~= d then
			return nil
		end
		total += d
	end
	local scale = math.clamp(math.floor(p.scale), 1, 8)
	local w, h = p.frame_w * scale, p.frame_h * scale
	local offset = math.clamp(p.offset_px, 0, 400)
	local name = safeName(p.name)
	local iteration = if p.loop then "infinite" else "1 forwards"
	local rule = table.concat({
		`{SELECTOR} \{`,
		'\tcontent: "";',
		"\tposition: absolute;",
		`\t{side.v}: {px(offset)};`,
		`\t{side.h}: {px(offset)};`,
		`\twidth: {px(w)};`,
		`\theight: {px(h)};`,
		"\tpointer-events: none;",
		-- Tern hides the layer while the pane shows a block; the animation stays.
		"\tvisibility: visible;",
		`\tz-index: {Z};`,
		"\timage-rendering: pixelated;",
		`\tbackground-image: url("{url}");`,
		"\tbackground-repeat: no-repeat;",
		`\tbackground-size: {px(w * n)} {px(h)};`,
		"\tbackground-position: 0px 0px;",
		`\tanimation: {name} {num(total)}ms step-end {iteration};`,
		"}",
	}, "\n")
	return table.concat({
		rule,
		keyframes(name, p.durations_ms, w),
		-- Tern's reduce_motion setting drives this query too.
		`@media (prefers-reduced-motion: reduce) \{ {SELECTOR} \{ display: none; } }`,
		"",
	}, "\n")
end

return {
	EMPTY = EMPTY,
	SELECTOR = SELECTOR,
	sheet = sheet,
}
