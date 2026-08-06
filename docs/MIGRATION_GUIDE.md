# Upgrade the existing GitHub repository

This package is designed as a code-and-demo upgrade for `Rae9711/cotiviti-policyguard`.

## Preserve first

Keep the existing final versions of:

- `report/`
- `slides/`
- `video/`
- any screenshots you still plan to use

The upgrade package contains empty placeholder folders for those deliverables so it can be merged without intentionally replacing them.

## Recommended merge

From the parent folder containing both repositories:

```bash
rsync -av \
  --exclude='.git/' \
  --exclude='report/' \
  --exclude='slides/' \
  --exclude='video/' \
  --exclude='screenshots/' \
  cotiviti-policyguard-v2/ cotiviti-policyguard/
```

Then enter the existing repository:

```bash
cd cotiviti-policyguard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make verify
streamlit run app.py
```

## Git workflow

```bash
git switch -c policyguard-v2

git add app.py src data tests scripts evaluation docs assets \
  .streamlit .github requirements.txt pyproject.toml Makefile README.md .gitignore

git commit -m "Redesign PolicyGuard as a source-grounded policy intelligence studio"
git push -u origin policyguard-v2
```

Review the branch in GitHub, update your report screenshots and presentation, then merge it to `main`.

## Before submission

- Replace any old screenshots with images from the working v2 application.
- Update report and slide metrics to match the generated synthetic run.
- Keep the MP4 under five minutes and directly in the repository.
- Confirm the resume, Word report, PowerPoint, and MP4 are all present and open correctly.
