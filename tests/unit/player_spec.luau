--!strict
local t = require("../lib/test")
local config = require("../../fx/config")
local css = require("../../fx/css")
local player = require("../../fx/player")

local describe, it, expect = t.describe, t.it, t.expect

local URL = "data:image/png;base64,AAAA"
-- Every sprite: two frames; loop 200 ms, endings 500 ms.
local DURATIONS = { loop = { 100, 100 }, success = { 250, 250 }, fail = { 250, 250 } }

type Timer = { at: number, fn: (focused: number?) -> (), cancelled: boolean }

local function harness(overrides: { [string]: any }?)
	local h = {
		now = 0,
		focused = 1 :: number?,
		sheets = {} :: { string },
		timers = {} :: { Timer },
		paused = false,
		cfg = config.defaults(),
		requested = {} :: { string },
		logs = {} :: { string },
	}
	for k, v in overrides or {} do
		(h :: any)[k] = v
	end
	h.p = player.new({
		css = function(source: string)
			table.insert(h.sheets, source)
		end,
		timer = function(ms: number, fn: (focused: number?) -> ()): () -> ()
			local timer: Timer = { at = h.now + ms, fn = fn, cancelled = false }
			table.insert(h.timers, timer)
			return function()
				timer.cancelled = true
			end
		end,
		config = function()
			return h.cfg
		end,
		paused = function()
			return h.paused
		end,
		sprite = function(command: string, phase: string)
			table.insert(h.requested, `{command}/{phase}`)
			if command == "blame" then
				return nil, "missing"
			end
			return { url = URL, frame_w = 32, frame_h = 32, durations_ms = (DURATIONS :: any)[phase] }, nil
		end,
		log = function(_level: string, message: string)
			table.insert(h.logs, message)
		end,
	})
	-- Runs due timers in time order up to now + ms.
	function h.advance(ms: number)
		local target = h.now + ms
		while true do
			local nextTimer: Timer? = nil
			for _, timer in h.timers do
				if not timer.cancelled and timer.at <= target and (nextTimer == nil or timer.at < nextTimer.at) then
					nextTimer = timer
				end
			end
			if nextTimer == nil then
				break
			end
			nextTimer.cancelled = true
			h.now = nextTimer.at
			nextTimer.fn(h.focused)
		end
		h.now = target
	end
	function h.started(pane: number, line: string)
		player.started(h.p, pane, line, h.focused)
	end
	function h.finished(pane: number, line: string, status: number)
		player.finished(h.p, pane, line, status, h.focused)
	end
	function h.focus(pane: number?)
		h.focused = pane
		player.focus(h.p, pane)
	end
	function h.last(): string?
		return h.sheets[#h.sheets]
	end
	return h
end

local function isLoop(sheet: string?): boolean
	return sheet ~= nil and string.find(sheet, "step-end infinite", 1, true) ~= nil
end

local function isEnding(sheet: string?): boolean
	return sheet ~= nil and string.find(sheet, "step-end 1 forwards", 1, true) ~= nil
end

describe("player", function()
	it("shows the loop once the command has run for loop_delay_ms", function()
		local h = harness()
		h.started(1, "git push")
		expect(#h.sheets).toBe(0)
		h.advance(299)
		expect(#h.sheets).toBe(0)
		h.advance(1)
		expect(isLoop(h.last())).toBeTruthy()
		expect(h.requested).toEqual({ "push/loop" })
	end)

	it("plays the success ending on exit 0, then clears after the frames plus hold_ms", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(1000)
		h.finished(1, "git push", 0)
		expect(isEnding(h.last())).toBeTruthy()
		expect(h.requested[#h.requested]).toBe("push/success")
		h.advance(500 + 900 - 1)
		expect(isEnding(h.last())).toBeTruthy()
		h.advance(1)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("plays the fail ending on a non-zero exit", function()
		local h = harness()
		h.started(1, "git pull")
		h.finished(1, "git pull", 128)
		expect(isEnding(h.last())).toBeTruthy()
		expect(h.requested[#h.requested]).toBe("pull/fail")
	end)

	it("skips the loop for a command faster than loop_delay_ms", function()
		local h = harness()
		h.started(1, "git add .")
		h.advance(50)
		h.finished(1, "git add .", 0)
		h.advance(1000)
		for _, sheet in h.sheets do
			expect(isLoop(sheet)).toBeFalsy()
		end
		expect(h.requested).notToContain("add/loop")
		expect(isEnding(h.sheets[1])).toBeTruthy()
	end)

	it("shows the loop at once with loop_delay_ms 0", function()
		local cfg = config.defaults()
		cfg.loop_delay_ms = 0
		local h = harness({ cfg = cfg })
		h.started(1, "git fetch")
		expect(isLoop(h.last())).toBeTruthy()
	end)

	it("restarts the animation with a new keyframes name for each new animation", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(300)
		h.finished(1, "git push", 0)
		local loopName = string.match(h.sheets[1], "@keyframes (%S+)")
		local endName = string.match(h.sheets[2], "@keyframes (%S+)")
		expect(loopName).notToBeNil()
		expect(endName).notToBeNil()
		expect(loopName ~= endName).toBeTruthy()
	end)

	it("ignores other commands, and their finish does not cut a git ending short", function()
		local h = harness()
		h.started(1, "ls -la")
		h.finished(1, "ls -la", 0)
		expect(#h.sheets).toBe(0)
		h.started(1, "git commit -m x")
		h.finished(1, "git commit -m x", 0)
		local count = #h.sheets
		h.started(1, "ls")
		h.finished(1, "ls", 1)
		expect(#h.sheets).toBe(count)
		expect(isEnding(h.last())).toBeTruthy()
	end)

	it("draws only the focused pane's animation and follows focus", function()
		local h = harness()
		h.started(1, "git clone url")
		h.advance(300)
		expect(isLoop(h.last())).toBeTruthy()
		h.focus(2)
		expect(h.last()).toBe(css.EMPTY)
		h.focus(1)
		expect(isLoop(h.last())).toBeTruthy()
	end)

	it("shows a loop running in a pane that was not focused when it started", function()
		local h = harness()
		h.focused = 2
		h.started(1, "git fetch")
		h.advance(300)
		expect(#h.sheets).toBe(0)
		h.focus(1)
		expect(isLoop(h.last())).toBeTruthy()
	end)

	it("does not replay an ending after focus leaves and returns", function()
		local h = harness()
		h.started(1, "git push")
		h.finished(1, "git push", 0)
		expect(isEnding(h.last())).toBeTruthy()
		h.focus(2)
		h.focus(1)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("never shows an ending that finished in an unfocused pane", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(300)
		h.focus(2)
		h.finished(1, "git push", 0)
		h.focus(1)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("does nothing while paused", function()
		local h = harness({ paused = true })
		h.started(1, "git push")
		h.advance(1000)
		h.finished(1, "git push", 0)
		expect(#h.sheets).toBe(0)
	end)

	it("pausing drops every animation, including the finish of a running one", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(300)
		h.paused = true
		player.clear(h.p)
		expect(h.last()).toBe(css.EMPTY)
		h.advance(10000)
		h.finished(1, "git push", 0)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("skips commands switched off in the config", function()
		local cfg = config.defaults()
		cfg.commands.push = false
		local h = harness({ cfg = cfg })
		h.started(1, "git push")
		h.advance(1000)
		h.finished(1, "git push", 0)
		expect(#h.sheets).toBe(0)
	end)

	it("plays the ending alone when the start was missed", function()
		local h = harness()
		h.finished(1, "git pull", 0)
		expect(isEnding(h.last())).toBeTruthy()
		expect(h.requested).notToContain("pull/loop")
	end)

	it("clears a closed pane", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(300)
		player.closed(h.p, 1, 2)
		expect(h.last()).toBe(css.EMPTY)
		h.focus(1)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("drops a loop whose finish never arrives", function()
		local h = harness()
		h.started(1, "git push")
		h.advance(300)
		h.advance(player.LOOP_MAX_MS)
		expect(h.last()).toBe(css.EMPTY)
	end)

	it("logs a missing sprite once and draws nothing", function()
		local h = harness()
		for _ = 1, 2 do
			h.started(1, "git blame f")
			h.advance(300)
			h.finished(1, "git blame f", 0)
			h.advance(5000)
		end
		for _, sheet in h.sheets do
			expect(sheet).toBe(css.EMPTY)
		end
		expect(#h.logs).toBe(2) -- blame/loop and blame/success
	end)
end)
