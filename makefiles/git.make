#
# help text for this module
#
help_git:
	@echo ""
	@echo "-------------------- Git: Setup ----------------------------"
	@echo "make git-install-hooks -------- Setup git hooks according to .pre-commit-config.yaml"
	@echo "make git-run-hooks ------------ Run all configured git pre-commit hooks without a commit"

#
# git targets
#
git-install-hooks:
	@echo "executing target git-install-hooks"
	@pre-commit install -t pre-commit -t post-commit

git-run-hooks:
	@echo "executing target git-run-hooks"
	@pre-commit run --all-files --hook-stage commit
