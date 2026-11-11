# Publishing to github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas

`repo/` holds exactly what goes on `main` of the LACUNA repo: `README.md` and `assets/overview.svg`.

Option A, in the browser (signed in as nhatlong113): open the repo, click **Add file → Upload files**, drag in `README.md` and the
`assets` folder from `repo/`, then commit directly to `main`.

Option B, with git, from a folder that contains this repository (`HMM-Develop`, branch `hmm-2nd-idea`):

    git clone https://github.com/nhatlong113/LACUNA---Localization-Aware-of-Coverage-and-UNmapped-Areas.git lacuna
    cd lacuna
    git am ../HMM-Develop/lacuna_release/lacuna_readme.patch
    git push origin main
