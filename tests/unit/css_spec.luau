--!strict
local t = require("../lib/test")
local css = require("../../fx/css")

local describe, it, expect = t.describe, t.it, t.expect

local URL = "data:image/png;base64,iVBORw0KGgo="

local function params(overrides: { [string]: any }?): css.Params
	local p: { [string]: any } = {
		name = "tern-git-fx-7",
		url = URL,
		frame_w = 32,
		frame_h = 32,
		durations_ms = { 100, 300 },
		loop = true,
		scale = 3,
		position = "bottom-right",
		offset_px = 20,
	}
	for k, v in overrides or {} do
		p[k] = v
	end
	return p :: any
end

describe("css.sheet", function()
	it("sizes the box and the strip by the scale", function()
		local s = css.sheet(params({ durations_ms = { 100, 100, 100, 100 } })) :: string
		expect(s).toContain(css.SELECTOR .. " {")
		expect(s).toContain("width: 96px;")
		expect(s).toContain("height: 96px;")
		expect(s).toContain("background-size: 384px 96px;")
		expect(s).toContain(`url("{URL}")`)
		expect(s).toContain("pointer-events: none;")
	end)

	it("places the box in the configured corner", function()
		local s = css.sheet(params({ position = "top-left", offset_px = 8 })) :: string
		expect(s).toContain("top: 8px;")
		expect(s).toContain("left: 8px;")
		expect(s).notToContain("bottom:")
		expect(s).notToContain("right:")
	end)

	it("holds each frame for its own duration", function()
		local s = css.sheet(params({ durations_ms = { 100, 300 } })) :: string
		expect(s).toContain("animation: tern-git-fx-7 400ms step-end infinite;")
		expect(s).toContain("0% { background-position: 0px 0px; }")
		expect(s).toContain("25% { background-position: -96px 0px; }")
		expect(s).toContain("100% { background-position: -96px 0px; }")
	end)

	it("plays an ending once and holds its last frame", function()
		local s = css.sheet(params({ loop = false })) :: string
		expect(s).toContain("step-end 1 forwards;")
		expect(s).notToContain("infinite")
	end)

	it("hides under reduced motion", function()
		local s = css.sheet(params()) :: string
		expect(s).toContain(`@media (prefers-reduced-motion: reduce) \{ {css.SELECTOR} \{ display: none; } }`)
	end)

	it("refuses anything that could inject CSS", function()
		expect(css.sheet(params({ url = 'data:image/png;base64,AAAA"); } * { display: none } x {' }))).toBeNil()
		expect(css.sheet(params({ url = "https://example.com/a.png" }))).toBeNil()
		expect(css.sheet(params({ position = "center" }))).toBeNil()
		expect(css.sheet(params({ durations_ms = {} }))).toBeNil()
		expect(css.sheet(params({ durations_ms = { 100, -1 } }))).toBeNil()
		local s = css.sheet(params({ name = "x} body {color:red" })) :: string
		expect(s).toContain("@keyframes xbodycolorred {")
		expect(s).toContain("animation: xbodycolorred ")
	end)

	it("clamps the scale and offset", function()
		local s = css.sheet(params({ scale = 50, offset_px = 9999 })) :: string
		expect(s).toContain("width: 256px;")
		expect(s).toContain("bottom: 400px;")
	end)
end)
