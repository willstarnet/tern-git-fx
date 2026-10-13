--!strict
local serde = require("@lune/serde")
local t = require("../lib/test")
local sprites = require("../../fx/sprites")

local describe, it, expect = t.describe, t.it, t.expect

local function u32be(n: number): string
	return string.char(bit32.extract(n, 24, 8), bit32.extract(n, 16, 8), bit32.extract(n, 8, 8), bit32.extract(n, 0, 8))
end

local function png(w: number, h: number): string
	return "\137PNG\r\n\26\n" .. u32be(13) .. "IHDR" .. u32be(w) .. u32be(h) .. "\8\6\0\0\0" .. "rest"
end

local function fixture(files: { [string]: string })
	local reads: { string } = {}
	local store = sprites.new({
		read = function(path: string, maxBytes: number): string
			table.insert(reads, path)
			local body = files[path]
			if body == nil then
				error(`no such file {path}`)
			end
			if #body > maxBytes then
				error("too big")
			end
			return body
		end,
		decode = function(text: string): any
			return serde.decode("json", text)
		end,
		base64 = function(bytes: string): string
			return serde.encode("json", #bytes)
		end,
	})
	return store, reads
end

local function manifest(entry: { [string]: any }): string
	return serde.encode("json", { schema = 1, frame_w = 32, frame_h = 32, commands = { push = entry } })
end

describe("sprites.get", function()
	it("loads a valid sheet as a data URL with its frame timing", function()
		local store = fixture({
			["assets/sprites/manifest.json"] = manifest({
				loop = { sheet = "push-loop.png", durations_ms = { 100, 200 } },
			}),
			["assets/sprites/push-loop.png"] = png(64, 32),
		})
		local sprite, err = sprites.get(store, "push", "loop")
		expect(err).toBeNil()
		local s = sprite :: sprites.Sprite
		expect(string.sub(s.url, 1, 22)).toBe("data:image/png;base64,")
		expect(s.frame_w).toBe(32)
		expect(s.frame_h).toBe(32)
		expect(s.durations_ms).toEqual({ 100, 200 })
	end)

	it("rejects a sheet whose size does not match its frame count", function()
		local store = fixture({
			["assets/sprites/manifest.json"] = manifest({
				loop = { sheet = "push-loop.png", durations_ms = { 100, 200 } },
			}),
			["assets/sprites/push-loop.png"] = png(96, 32),
		})
		local sprite, err = sprites.get(store, "push", "loop")
		expect(sprite).toBeNil()
		expect(err).toContain("is not 2 frames of 32x32")
	end)

	it("rejects non-PNG data, path tricks and out-of-range timing", function()
		local store = fixture({
			["assets/sprites/manifest.json"] = manifest({
				loop = { sheet = "push-loop.png", durations_ms = { 100, 200 } },
				success = { sheet = "../../secret.png", durations_ms = { 100, 100, 100, 300 } },
				fail = { sheet = "push-fail.png", durations_ms = { 100, 10 } },
			}),
			["assets/sprites/push-loop.png"] = "GIF89a....................",
		})
		expect(select(2, sprites.get(store, "push", "loop"))).toContain("is not a PNG")
		expect(select(2, sprites.get(store, "push", "success"))).toContain("bad sheet name")
		expect(select(2, sprites.get(store, "push", "fail"))).toContain("bad durations")
		expect(select(2, sprites.get(store, "pull", "loop"))).toContain("no loop animation for pull")
	end)

	it("reports an unreadable manifest without crashing", function()
		local store = fixture({ ["assets/sprites/manifest.json"] = "{not json" })
		local sprite, err = sprites.get(store, "push", "loop")
		expect(sprite).toBeNil()
		expect(err).toContain("manifest.json unreadable")
	end)

	it("reads each file once, failures included", function()
		local store, reads = fixture({
			["assets/sprites/manifest.json"] = manifest({
				loop = { sheet = "push-loop.png", durations_ms = { 100, 200 } },
			}),
			["assets/sprites/push-loop.png"] = png(64, 32),
		})
		for _ = 1, 3 do
			sprites.get(store, "push", "loop")
			sprites.get(store, "push", "fail")
		end
		expect(reads).toEqual({ "assets/sprites/manifest.json", "assets/sprites/push-loop.png" })
	end)
end)
