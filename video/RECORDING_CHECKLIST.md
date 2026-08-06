# Recording Checklist (Cotiviti Assessment Rules)

Use this before you upload the video into the public GitHub repository.

## Cotiviti submission rules (from official instructions)

- [ ] Video is an **MP4** file  
- [ ] Length is **no longer than five minutes**  
- [ ] You **appear on camera** as the presenter  
- [ ] Content includes **PowerPoint overview** + **screenshare of the working POC**  
- [ ] Video file is uploaded **into the public GitHub repo** (path suggestion: `video/PolicyGuard_Demo.mp4`)  
- [ ] **Do not** rely on Google Drive, YouTube, or other external links (blocked on Cotiviti network)

## Technical prep

- [ ] `source .venv/bin/activate && streamlit run app.py` works without an API key  
- [ ] `pytest -q` passes  
- [ ] Slides open: `slides/PolicyGuard_Presentation.pptx`  
- [ ] Browser zoom set for readability; dark/light theme comfortable on camera  
- [ ] Microphone levels checked; camera framing includes face + upper torso  

## Content checklist

- [ ] Spoken disclaimer (HITL; no autonomous denial)  
- [ ] Topic 3 named; PolicyGuard one-sentence pitch  
- [ ] Demo shows diff, grounded evidence, JSON rule, Approve → claim flags, abstention path  
- [ ] Evaluation numbers match `evaluation/results.md` (do not invent)  
- [ ] Careful claim language only  

## After recording

- [ ] Export/save as `video/PolicyGuard_Demo.mp4` (or similar clear name)  
- [ ] Confirm file size is reasonable for GitHub (use Git LFS if needed for large MP4s)  
- [ ] Commit/push only when you are ready (not done automatically by the assessment build agent)  
- [ ] Email `jesus.hurtado@cotiviti.com` with subject:  
  `INTERN - [Position Applied For] - [Full Name] - [University Name]`  
  and include the public repository link  

## Not done by the agent

- On-camera recording (candidate only)  
- Final GitHub remote/push and submission email (candidate only)
