--!strict
-- Loads the bundled sprite sheets named by assets/sprites/manifest.json as data URLs, validating
-- the manifest and each PNG's size, and caching every result (failures too, so a broken asset is
-- reported once). File access is injected.

export type Phase = "loop" | "success" | "fail"

export type Sprite = {
	url: string,
	frame_w: number,
	frame_h: number,
	durations_ms: { number },
}

export type Ports = {
	-- Reads a file under the plugin directory (`max_bytes` caps the read); raises on failure.
	read: (path: string, max_bytes: number) -> string,
	decode: (text: string) -> any,
	base64: (bytes: string) -> string,
}

export type Store = {
	ports: Ports,
	manifest: any,
	manifest_error: string?,
	cache: { [string]: Sprite | string },
}

local DIR = "assets/sprites/"
local MAX_MANIFEST_BYTES = 64 * 1024
local MAX_SHEET_BYTES = 512 * 1024
local MAX_FRAME_PX = 128
-- Same limits as tools/build_sprites.py.
local LIMITS: { [string]: { frames: { number }, frame_ms: { number }, total_ms: { number } } } = {
	loop = { frames = { 2, 12 }, frame_ms = { 60, 1000 }, total_ms = { 300, 2400 } },
	success = { frames = { 4, 20 }, frame_ms = { 40, 1500 }, total_ms = { 500, 2600 } },
	fail = { frames = { 4, 20 }, frame_ms = { 40, 1500 }, total_ms = { 500, 2600 } },
}
local PNG_SIGNATURE = "\137PNG\r\n\26\n"

local function new(ports: Ports): Store
	return { ports = ports, manifest = nil, manifest_error = nil, cache = {} }
end

local function positiveInt(v: any, max: number): boolean
	return type(v) == "number" and v == math.floor(v) and v >= 1 and v <= max
end

local function loadManifest(store: Store): (any, string?)
	if store.manifest ~= nil or store.manifest_error ~= nil then
		return store.manifest, store.manifest_error
	end
	local ok, result = pcall(function()
		return store.ports.decode(store.ports.read(DIR .. "manifest.json", MAX_MANIFEST_BYTES))
	end)
	local err: string? = nil
	if not ok then
		err = `manifest.json unreadable: {tostring(result)}`
	elseif type(result) ~= "table" or result.schema ~= 1 then
		err = "manifest.json: expected schema 1"
	elseif not positiveInt(result.frame_w, MAX_FRAME_PX) or not positiveInt(result.frame_h, MAX_FRAME_PX) then
		err = "manifest.json: bad frame size"
	elseif type(result.commands) ~= "table" then
		err = "manifest.json: missing commands"
	end
	if err then
		store.manifest_error = err
		return nil, err
	end
	store.manifest = result
	return result, nil
end

local function u32be(bytes: string, at: number): number
	local a, b, c, d = string.byte(bytes, at, at + 3)
	return ((a or 0) * 16777216) + ((b or 0) * 65536) + ((c or 0) * 256) + (d or 0)
end

local function validDurations(phase: string, durations: any): { number }?
	local lim = LIMITS[phase]
	if lim == nil or type(durations) ~= "table" then
		return nil
	end
	local out: { number } = {}
	local total = 0
	for _, d in durations do
		if type(d) ~= "number" or d < lim.frame_ms[1] or d > lim.frame_ms[2] then
			return nil
		end
		total += d
		table.insert(out, d)
	end
	if #out < lim.frames[1] or #out > lim.frames[2] or total < lim.total_ms[1] or total > lim.total_ms[2] then
		return nil
	end
	return out
end

local function load(store: Store, command: string, phase: Phase): Sprite | string
	local manifest, err = loadManifest(store)
	if err then
		return err
	end
	local entry = manifest.commands[command]
	entry = if type(entry) == "table" then entry[phase] else nil
	if type(entry) ~= "table" then
		return `no {phase} animation for {command}`
	end
	local sheet = entry.sheet
	if type(sheet) ~= "string" or not string.match(sheet, "^[a-z0-9%-]+%.png$") then
		return `{command}/{phase}: bad sheet name`
	end
	local durations = validDurations(phase, entry.durations_ms)
	if durations == nil then
		return `{command}/{phase}: bad durations`
	end
	local ok, bytes = pcall(store.ports.read, DIR .. sheet, MAX_SHEET_BYTES)
	if not ok then
		return `{sheet} unreadable: {tostring(bytes)}`
	end
	local fw, fh = manifest.frame_w, manifest.frame_h
	if string.sub(bytes, 1, 8) ~= PNG_SIGNATURE or string.sub(bytes, 13, 16) ~= "IHDR" then
		return `{sheet} is not a PNG`
	end
	if u32be(bytes, 17) ~= fw * #durations or u32be(bytes, 21) ~= fh then
		return `{sheet} is not {#durations} frames of {fw}x{fh}`
	end
	return {
		url = "data:image/png;base64," .. store.ports.base64(bytes),
		frame_w = fw,
		frame_h = fh,
		durations_ms = durations,
	}
end

-- The sprite for `command`'s `phase`, or nil and why not.
local function get(store: Store, command: string, phase: Phase): (Sprite?, string?)
	local key = command .. "/" .. phase
	local hit = store.cache[key]
	if hit == nil then
		hit = load(store, command, phase)
		store.cache[key] = hit
	end
	if type(hit) == "string" then
		return nil, hit
	end
	return hit, nil
end

return {
	new = new,
	get = get,
}
