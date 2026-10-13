--!strict
local t = require("../lib/test")
local classify = require("../../fx/classify")

local describe, it, expect = t.describe, t.it, t.expect

local function expectAll(want: string?, lines: { string }, aliases: classify.Aliases?)
	for _, line in lines do
		local got = classify.classify(line, aliases)
		if got ~= want then
			error(`classify({string.format("%q", line)}) = {tostring(got)}, expected {tostring(want)}`, 2)
		end
	end
end

describe("classify", function()
	it("recognizes each supported subcommand", function()
		for _, c in classify.COMMANDS do
			expectAll(c, { `git {c}`, `git {c} --some-flag arg` })
		end
	end)

	it("maps switch to checkout and stage to add", function()
		expectAll("checkout", { "git switch main", "git switch -c feature" })
		expectAll("add", { "git stage -p" })
	end)

	it("skips git global options, including ones that take a value", function()
		expectAll("push", { "git -C ../repo push", "git -C ../push status && git -C x push" })
		expectAll("commit", { 'git -c user.name="A B" commit -m x', "git -c core.editor=vim commit" })
		expectAll("blame", { "git --no-pager blame file.txt", "git -P blame f" })
		expectAll("fetch", { "git --git-dir=.git --work-tree=. fetch", "git --git-dir .git fetch" })
	end)

	it("does not take a global option's value for the subcommand", function()
		expectAll(nil, { "git -C push status", "git -c push=1 log" })
	end)

	it("sees through program paths, assignments, redirections and wrappers", function()
		expectAll("pull", { "/usr/bin/git pull", "/opt/homebrew/bin/git pull --rebase" })
		expectAll("push", {
			"GIT_TRACE=1 git push",
			"A=1 B=2 git push origin main",
			"sudo git push",
			"sudo -u deploy git push",
			"env -u HOME FOO=1 git push",
			"command git push",
			"time git push",
			"nice -n 10 git push",
			"noglob git push",
		})
	end)

	it("picks the last git command of a list", function()
		expectAll("push", {
			'git add -A && git commit -m "wip" && git push',
			"git fetch; git push",
			"git pull || git push",
			"git stash & git push",
		})
		expectAll("commit", { "git push && ls && git commit" })
	end)

	it("finds git commands in pipelines, subshells and groups", function()
		expectAll("branch", { "git branch | grep main", "git branch -a | less" })
		expectAll("push", { "git push 2>&1 | tee push.log", "git push >/dev/null 2>&1" })
		expectAll("pull", { "(cd repo && git pull)", "{ git pull; }" })
	end)

	it("ignores separators and git words inside quotes", function()
		expectAll("commit", {
			'git commit -m "fix; then git push"',
			"git commit -m 'a && git push'",
			'git commit -m "say \\"git push\\""',
		})
		expectAll(nil, { 'echo "git push"', "echo 'git push'" })
	end)

	it("returns nil for anything that is not one of the commands", function()
		expectAll(nil, {
			"",
			"ls -la",
			"git",
			"git status",
			"git log --oneline",
			"git help push",
			"git --version",
			"gitk",
			"github push",
			"cat push",
			"rm -rf git",
		})
		expect(classify.classify(nil)).toBeNil()
		expect(classify.classify(42)).toBeNil()
		expect(classify.classify(string.rep("a", 9000))).toBeNil()
	end)

	it("knows the oh-my-zsh git aliases and g=git", function()
		expectAll("push", { "gp", "gpsup", "gpf!", "ggpush", "gp origin main" })
		expectAll("commit", { 'gcmsg "msg"', "gc", "gca!", "gcn!" })
		expectAll("checkout", { "gco main", "gcb feature", "gsw main" })
		expectAll("pull", { "gl", "gpr", "ggl" })
		expectAll("stash", { "gsta", "gstp", "gstl" })
		expectAll("reset", { "grhh", "gpristine" })
		expectAll("fetch", { "gfa", "gf" })
		expectAll("clone", { "gcl https://example.com/r.git", "gccd url" })
		expectAll("push", { "g push", "g -C x push" })
	end)

	it("knows common git config aliases", function()
		expectAll("checkout", { "git co main", "git sw main" })
		expectAll("commit", { "git ci -m x" })
		expectAll("branch", { "git br -d x" })
	end)

	it("uses caller alias tables, where false removes a built-in", function()
		local aliases = classify.defaultAliases()
		aliases.shell.gp = false
		aliases.shell.ship = "push"
		aliases.git.co = false
		aliases.git.save = "commit"
		expectAll(nil, { "gp", "git co main" }, aliases)
		expectAll("push", { "ship" }, aliases)
		expectAll("commit", { "git save" }, aliases)
		-- the built-ins are copies: the defaults are unchanged
		expectAll("push", { "gp" })
	end)

	it("lets a shell alias named g take precedence over g=git", function()
		local aliases = classify.defaultAliases()
		aliases.shell.g = "fetch"
		expectAll("fetch", { "g" }, aliases)
	end)
end)

describe("split", function()
	it("keeps quoted text in one word and drops the quotes", function()
		expect(classify.split([[git commit -m "a b" -m 'c d' e\ f]])).toEqual({
			{ "git", "commit", "-m", "a b", "-m", "c d", "e f" },
		})
	end)

	it("keeps an empty quoted argument", function()
		expect(classify.split([[git commit -m ""]])).toEqual({ { "git", "commit", "-m", "" } })
	end)
end)
