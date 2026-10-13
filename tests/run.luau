--!strict
-- Loads tests/unit/*_spec.luau and runs every case, or only those whose name contains the
-- first argument. Run from the repository root: lune run tests/run.luau [filter]

local fs = require("@lune/fs")
local process = require("@lune/process")
local stdio = require("@lune/stdio")
local t = require("./lib/test")

local SPECS = "tests/unit"

if not fs.isDir(SPECS) then
	stdio.ewrite("run from the repository root: lune run tests/run.luau\n")
	process.exit(2)
end

local files = fs.readDir(SPECS)
table.sort(files)
local loaded = 0
for _, file in files do
	if string.match(file, "_spec%.luau$") then
		require("./unit/" .. string.gsub(file, "%.luau$", ""))
		loaded += 1
	end
end

local filter = process.args[1]
local ran, failed = 0, 0
for _, case in t.registered() do
	if filter == nil or string.find(case.name, filter, 1, true) then
		ran += 1
		local ok, err = pcall(case.run)
		if not ok then
			failed += 1
			stdio.ewrite(`not ok: {case.name}\n  {tostring(err)}\n`)
		end
	end
end

print(`{loaded} spec files, {ran} cases, {ran - failed} passed, {failed} failed`)
if failed > 0 or ran == 0 then
	process.exit(1)
end
