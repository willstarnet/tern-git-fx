--!strict
local serde = require("@lune/serde")
local t = require("../lib/test")
local config = require("../../fx/config")
local classify = require("../../fx/classify")

local describe, it, expect = t.describe, t.it, t.expect

local function hasWarning(warnings: { string }, fragment: string): boolean
	for _, w in warnings do
		if string.find(w, fragment, 1, true) then
			return true
		end
	end
	return false
end

describe("config.resolve", function()
	it("gives the defaults with no file", function()
		local cfg, warnings = config.resolve(nil)
		expect(warnings).toEqual({})
		expect(cfg).toEqual(config.defaults())
		for _, c in classify.COMMANDS do
			expect(cfg.commands[c]).toBe(true)
		end
	end)

	it("applies valid values", function()
		local cfg, warnings = config.resolve({
			position = "top-left",
			offset_px = 4.5,
			scale = 2,
			loop_delay_ms = 0,
			hold_ms = 2000,
			commands = { blame = false, push = true },
		})
		expect(warnings).toEqual({})
		expect(cfg.position).toBe("top-left")
		expect(cfg.offset_px).toBe(4.5)
		expect(cfg.scale).toBe(2)
		expect(cfg.loop_delay_ms).toBe(0)
		expect(cfg.hold_ms).toBe(2000)
		expect(cfg.commands.blame).toBe(false)
		expect(cfg.commands.push).toBe(true)
		expect(cfg.commands.commit).toBe(true)
	end)

	it("falls back field by field and says why", function()
		local d = config.defaults()
		local cfg, warnings = config.resolve({
			position = "middle",
			scale = 2.5,
			offset_px = -1,
			hold_ms = "long",
			loop_delay_ms = 0 / 0,
			commands = { push = "yes", status = true },
			colour = "red",
		})
		expect(cfg.position).toBe(d.position)
		expect(cfg.scale).toBe(d.scale)
		expect(cfg.offset_px).toBe(d.offset_px)
		expect(cfg.hold_ms).toBe(d.hold_ms)
		expect(cfg.loop_delay_ms).toBe(d.loop_delay_ms)
		expect(cfg.commands.push).toBe(true)
		expect(hasWarning(warnings, "position")).toBeTruthy()
		expect(hasWarning(warnings, "scale: expected an integer from 1 to 8")).toBeTruthy()
		expect(hasWarning(warnings, "offset_px")).toBeTruthy()
		expect(hasWarning(warnings, "hold_ms")).toBeTruthy()
		expect(hasWarning(warnings, "loop_delay_ms")).toBeTruthy()
		expect(hasWarning(warnings, "commands.push: expected true or false")).toBeTruthy()
		expect(hasWarning(warnings, "unknown command status")).toBeTruthy()
		expect(hasWarning(warnings, "unknown key colour")).toBeTruthy()
	end)

	it("rejects a file that is not an object", function()
		local cfg, warnings = config.resolve("hello")
		expect(cfg).toEqual(config.defaults())
		expect(#warnings).toBe(1)
	end)

	it("overlays aliases on the built-ins; false removes one", function()
		local cfg, warnings = config.resolve({
			aliases = { ship = "push", gp = false, oops = "status", ["bad name"] = "push" },
			git_aliases = { save = "commit", co = false },
		})
		expect(cfg.aliases.shell.ship).toBe("push")
		expect(cfg.aliases.shell.gp).toBe(false)
		expect(cfg.aliases.shell.gl).toBe("pull")
		expect(cfg.aliases.shell.oops).toBeNil()
		expect(cfg.aliases.git.save).toBe("commit")
		expect(cfg.aliases.git.co).toBe(false)
		expect(hasWarning(warnings, "aliases.oops")).toBeTruthy()
		expect(hasWarning(warnings, "invalid alias name bad name")).toBeTruthy()
		expect(classify.classify("ship", cfg.aliases)).toBe("push")
		expect(classify.classify("gp", cfg.aliases)).toBeNil()
		-- resolving does not leak into the next resolve
		expect(config.resolve(nil).aliases.shell.gp).toBe("push")
	end)
end)

describe("config.starterText", function()
	it("is JSON that resolves to the defaults without warnings", function()
		local raw = serde.decode("json", config.starterText())
		local cfg, warnings = config.resolve(raw)
		expect(warnings).toEqual({})
		expect(cfg).toEqual(config.defaults())
	end)
end)
