--!strict
-- A small spec library for Lune: `describe` groups, `it` registers a case, `expect` asserts.
-- tests/run.luau loads every spec file and runs the registered cases.

export type Case = { name: string, run: () -> () }

local cases: { Case } = {}
local groups: { string } = {}

local function describe(name: string, body: () -> ())
	table.insert(groups, name)
	body()
	table.remove(groups)
end

local function it(name: string, run: () -> ())
	local path = table.clone(groups)
	table.insert(path, name)
	table.insert(cases, { name = table.concat(path, " / "), run = run })
end

-- A readable, deterministic rendering of a value for failure messages.
local function show(v: any, depth: number?): string
	local d = depth or 0
	if type(v) == "string" then
		return string.format("%q", v)
	elseif type(v) ~= "table" then
		return tostring(v)
	elseif d >= 4 then
		return "{…}"
	end
	local keys = {}
	for k in v do
		table.insert(keys, k)
	end
	table.sort(keys, function(a, b)
		return tostring(a) < tostring(b)
	end)
	local parts = {}
	for _, k in keys do
		table.insert(parts, `{tostring(k)}: {show(v[k], d + 1)}`)
	end
	return "{ " .. table.concat(parts, ", ") .. " }"
end

local function same(a: any, b: any): boolean
	if a == b then
		return true
	end
	if type(a) ~= "table" or type(b) ~= "table" then
		return false
	end
	for k, v in a do
		if not same(v, b[k]) then
			return false
		end
	end
	for k in b do
		if a[k] == nil then
			return false
		end
	end
	return true
end

-- Whether `haystack` (a string, or a list compared deeply) contains `needle`.
local function contains(haystack: any, needle: any): boolean
	if type(haystack) == "string" then
		return type(needle) == "string" and string.find(haystack, needle, 1, true) ~= nil
	end
	if type(haystack) == "table" then
		for _, v in haystack do
			if same(v, needle) then
				return true
			end
		end
	end
	return false
end

local function check(ok: boolean, message: string)
	if not ok then
		-- level 3: the spec line that called the matcher
		error(message, 3)
	end
end

local function expect(actual: any)
	return {
		toBe = function(want: any)
			check(actual == want, `got {show(actual)}, want {show(want)}`)
		end,
		toEqual = function(want: any)
			check(same(actual, want), `got {show(actual)}, want (deeply) {show(want)}`)
		end,
		toBeNil = function()
			check(actual == nil, `got {show(actual)}, want nil`)
		end,
		notToBeNil = function()
			check(actual ~= nil, "got nil")
		end,
		toBeTruthy = function()
			check(not not actual, `got {show(actual)}, want a truthy value`)
		end,
		toBeFalsy = function()
			check(not actual, `got {show(actual)}, want a falsy value`)
		end,
		toContain = function(needle: any)
			check(contains(actual, needle), `{show(actual)} does not contain {show(needle)}`)
		end,
		notToContain = function(needle: any)
			check(not contains(actual, needle), `{show(actual)} contains {show(needle)}`)
		end,
	}
end

local function registered(): { Case }
	return cases
end

return {
	describe = describe,
	it = it,
	expect = expect,
	registered = registered,
}
