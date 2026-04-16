# MSR4Agent Research Project

Paper link: <https://www.overleaf.com/2188544256gcwhncrfvjqt#178607>

## Managing the Paper Submodule

The research paper is hosted on Overleaf and is tracked in this repository as a Git submodule in the `paper/` directory.

To clone this repository along with the paper:

```shell
# 0. Configure credentials to push/pull from Overleaf
git config --global credential.helper store
# Note: You must generate a personal access token in your Overleaf account settings for authentication.

# 1. Clone the repository and fetch submodules
git clone --recursive <repository-url>
cd msr4agent
```

If you have already cloned this repository without the `--recursive` flag, you can initialize the submodule by running:

```shell
git submodule update --init --recursive
```
