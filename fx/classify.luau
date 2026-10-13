--!strict
-- Reduces a shell command line to the git command it runs, if any. Pure.
--
-- The line is split into simple commands at `;`, `&&`, `||`, `|`, `&`, newlines and parentheses
-- (outside quotes). In each, leading `VAR=value` words and wrapper programs (`sudo`, `env`,
-- `command`, ...) are skipped, then the program is matched: `git` (or `g`) with its global
-- options skipped and the subcommand looked up, or a shell alias. The last git command on the
-- line wins: in `git add -A && git commit && git push` the push is what the user waits for.

-- One of COMMANDS: commit, push, pull, fetch, add, restore, init, clone, branch, checkout,
-- stash, blame, reset.
export type Command = string

-- Alias name -> command; `false` removes an alias (a user's config can unset a built-in one).
export type AliasMap = { [string]: Command | false }

export type Aliases = {
	-- First word of a simple command (shell aliases and functions): `gp` -> push.
	shell: AliasMap,
	-- Word after `git` (git config `alias.*`): `git co` -> checkout.
	git: AliasMap,
}

local COMMANDS: { Command } = {
	"commit",
	"push",
	"pull",
	"fetch",
	"add",
	"restore",
	"init",
	"clone",
	"branch",
	"checkout",
	"stash",
	"blame",
	"reset",
}

local IS_COMMAND: { [string]: Command } = {}
for _, c in COMMANDS do
	IS_COMMAND[c] = c
end

-- Built-in git subcommands that do the same job as one of ours.
local SYNONYMS: { [string]: Command } = {
	switch = "checkout",
	stage = "add",
}

-- Programs that run the rest of the line as a command, and their options that take a value.
local WRAPPERS: { [string]: { [string]: boolean } } = {
	sudo = {
		["-u"] = true,
		["-g"] = true,
		["-C"] = true,
		["-D"] = true,
		["-h"] = true,
		["-p"] = true,
		["-r"] = true,
		["-t"] = true,
		["-U"] = true,
	},
	doas = { ["-u"] = true, ["-C"] = true },
	env = { ["-u"] = true, ["-C"] = true, ["-S"] = true },
	nice = { ["-n"] = true },
	time = { ["-f"] = true, ["-o"] = true },
	exec = { ["-a"] = true },
	nohup = {},
	command = {},
	builtin = {},
	caffeinate = { ["-t"] = true, ["-w"] = true },
	noglob = {},
	nocorrect = {},
}

-- git global options (before the subcommand) that take the next word as their value.
local GIT_VALUE_OPTIONS: { [string]: boolean } = {
	["-C"] = true,
	["-c"] = true,
	["--git-dir"] = true,
	["--work-tree"] = true,
	["--namespace"] = true,
	["--super-prefix"] = true,
	["--config-env"] = true,
	["--attr-source"] = true,
}

-- Common `git config alias.*` shorthands.
local GIT_ALIASES: AliasMap = {
	co = "checkout",
	ci = "commit",
	br = "branch",
	cl = "clone",
	rs = "restore",
	sw = "checkout",
}

-- The oh-my-zsh git plugin's aliases and functions for these commands
-- (https://github.com/ohmyzsh/ohmyzsh/blob/master/plugins/git/git.plugin.zsh).
local SHELL_ALIASES: AliasMap = {
	-- add
	ga = "add",
	gaa = "add",
	gapa = "add",
	gau = "add",
	gav = "add",
	-- blame
	gbl = "blame",
	-- branch
	gb = "branch",
	gba = "branch",
	gbd = "branch",
	gbD = "branch",
	gbm = "branch",
	gbnm = "branch",
	gbr = "branch",
	gbda = "branch",
	gbds = "branch",
	gbg = "branch",
	gbgD = "branch",
	ggsup = "branch",
	-- checkout / switch
	gco = "checkout",
	gcor = "checkout",
	gcb = "checkout",
	gcB = "checkout",
	gcd = "checkout",
	gcm = "checkout",
	gsw = "checkout",
	gswc = "checkout",
	gswd = "checkout",
	gswm = "checkout",
	-- clone
	gcl = "clone",
	gclf = "clone",
	gccd = "clone",
	-- commit
	gc = "commit",
	["gc!"] = "commit",
	gca = "commit",
	["gca!"] = "commit",
	["gcan!"] = "commit",
	["gcans!"] = "commit",
	["gcann!"] = "commit",
	gcam = "commit",
	gcas = "commit",
	gcasm = "commit",
	gcs = "commit",
	gcss = "commit",
	gcssm = "commit",
	gcmsg = "commit",
	gcsm = "commit",
	gcn = "commit",
	["gcn!"] = "commit",
	gcfu = "commit",
	gwip = "commit",
	-- fetch
	gf = "fetch",
	gfa = "fetch",
	gfo = "fetch",
	-- pull
	gl = "pull",
	ggl = "pull",
	ggu = "pull",
	ggpull = "pull",
	gluc = "pull",
	glum = "pull",
	gpr = "pull",
	gprv = "pull",
	gpra = "pull",
	gprav = "pull",
	gprom = "pull",
	gpromi = "pull",
	gprum = "pull",
	gprumi = "pull",
	-- push
	gp = "push",
	gpd = "push",
	gpf = "push",
	["gpf!"] = "push",
	gpsup = "push",
	gpsupf = "push",
	gpv = "push",
	gpoat = "push",
	gpod = "push",
	gpu = "push",
	ggp = "push",
	ggf = "push",
	ggfl = "push",
	ggpush = "push",
	ggpnp = "push",
	-- reset
	grh = "reset",
	gru = "reset",
	grhh = "reset",
	grhk = "reset",
	grhs = "reset",
	groh = "reset",
	gpristine = "reset",
	gwipe = "reset",
	-- restore
	grs = "restore",
	grss = "restore",
	grst = "restore",
	-- stash
	gsta = "stash",
	gstaa = "stash",
	gstall = "stash",
	gstc = "stash",
	gstd = "stash",
	gstl = "stash",
	gstp = "stash",
	gsts = "stash",
	gstu = "stash",
}

-- Fresh copies of the built-in alias tables.
local function defaultAliases(): Aliases
	return { shell = table.clone(SHELL_ALIASES), git = table.clone(GIT_ALIASES) }
end

local function isCommand(v: any): boolean
	return type(v) == "string" and IS_COMMAND[v] ~= nil
end

-- Splits a line into simple commands (lists of words), honoring quotes and backslashes.
local function split(line: string): { { string } }
	local segments: { { string } } = {}
	local words: { string } = {}
	local word = {}
	local inWord = false
	local quote: string? = nil
	local i, n = 1, #line

	local function endWord()
		if inWord then
			table.insert(words, table.concat(word))
			table.clear(word)
			inWord = false
		end
	end
	local function endSegment()
		endWord()
		if #words > 0 then
			table.insert(segments, words)
			words = {}
		end
	end

	while i <= n do
		local ch = string.sub(line, i, i)
		if quote == "'" then
			if ch == "'" then
				quote = nil
			else
				table.insert(word, ch)
			end
		elseif quote == '"' then
			if ch == '"' then
				quote = nil
			elseif ch == "\\" and i < n then
				i += 1
				table.insert(word, string.sub(line, i, i))
			else
				table.insert(word, ch)
			end
		elseif ch == "'" or ch == '"' then
			quote = ch
			inWord = true
		elseif ch == "\\" then
			if i < n then
				i += 1
				table.insert(word, string.sub(line, i, i))
				inWord = true
			end
		elseif ch == " " or ch == "\t" then
			endWord()
		elseif
			ch == ";"
			or ch == "|"
			or ch == "\n"
			or ch == "\r"
			or ch == "("
			or ch == ")"
			or ch == "{"
			or ch == "}"
		then
			endSegment()
		elseif ch == "&" then
			local prev = word[#word]
			if inWord and (prev == ">" or prev == "<") then
				-- `2>&1`, `>&2`: part of a redirection, not a list operator
				table.insert(word, ch)
			else
				endSegment()
			end
		else
			table.insert(word, ch)
			inWord = true
		end
		i += 1
	end
	endSegment()
	return segments
end

local function basename(path: string): string
	return string.match(path, "([^/]+)$") or path
end

local function isAssignment(w: string): boolean
	return string.match(w, "^[%a_][%w_]*=") ~= nil
end

local function isRedirection(w: string): boolean
	return string.match(w, "^%d*[<>]") ~= nil or string.match(w, "^&>") ~= nil
end

-- The subcommand after `git` at words[i], or nil.
local function gitCommand(words: { string }, i: number, gitAliases: AliasMap): Command?
	while i <= #words do
		local w = words[i]
		if isRedirection(w) then
			i += 1
		elseif string.sub(w, 1, 1) == "-" then
			if GIT_VALUE_OPTIONS[w] == true then
				i += 2
			else
				i += 1
			end
		else
			local direct = IS_COMMAND[w] or SYNONYMS[w]
			if direct then
				return direct
			end
			local alias = gitAliases[w]
			if isCommand(alias) then
				return alias :: Command
			end
			return nil
		end
	end
	return nil
end

-- The git command a simple command runs, or nil.
local function segmentCommand(words: { string }, aliases: Aliases): Command?
	local i = 1
	while i <= #words do
		local w = words[i]
		if isAssignment(w) or isRedirection(w) then
			i += 1
			continue
		end
		local valueOptions = WRAPPERS[basename(w)]
		if valueOptions == nil then
			break
		end
		i += 1
		while i <= #words do
			local opt = words[i]
			if valueOptions[opt] then
				i += 2
			elseif string.sub(opt, 1, 1) == "-" or isAssignment(opt) then
				i += 1
			else
				break
			end
		end
	end
	local program = words[i]
	if program == nil then
		return nil
	end
	local name = basename(program)
	if name == "git" or name == "git.exe" then
		return gitCommand(words, i + 1, aliases.git)
	end
	local alias = aliases.shell[name]
	if alias == nil and name == "g" then
		-- the common `alias g=git`
		return gitCommand(words, i + 1, aliases.git)
	end
	if isCommand(alias) then
		return alias :: Command
	end
	return nil
end

-- The git command `line` runs (the last one on the line), or nil.
local function classify(line: any, aliases: Aliases?): Command?
	if type(line) ~= "string" or line == "" or #line > 8192 then
		return nil
	end
	local a = aliases or defaultAliases()
	local found: Command? = nil
	for _, words in split(line) do
		local c = segmentCommand(words, a)
		if c then
			found = c
		end
	end
	return found
end

return {
	COMMANDS = COMMANDS,
	classify = classify,
	defaultAliases = defaultAliases,
	isCommand = isCommand,
	split = split,
}
