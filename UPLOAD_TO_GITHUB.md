# Upload / replace the existing repository

Review the files first, then from this repository directory:

```bash
git init
git add .
git commit -m "Rebuild explorer as archive research prototype"
git branch -M main
git remote add origin https://github.com/ihendrix/software-heritage-dataset-explorer.git
git push -u origin main --force-with-lease
```

If you want to preserve the existing repository history instead, copy these files over your current clone, then use a normal commit and push rather than initializing a new repository.

Before publishing, do **not** commit `.env`, API keys, or the local ORC dataset. The supplied `.gitignore` excludes them.
