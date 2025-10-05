# Getting Help with Maps4FS

## 🆕 Interactive Help Tool (Recommended)

**The easiest way to get help is using our interactive help page:**

- **Local Deployment:** `http://localhost:3000/help`
- **Public App:** [http://maps4fs.xyz/help](http://maps4fs.xyz/help)

This interactive tool will:
- ✅ Guide## 📋 Quick Reference Guide

| 🎯 Scenario | 🔄 Action |
|-------------|-----------|
| 🆕 **Any issue** | 🎯 **Use Interactive Help Tool first** (`/help` page) |
| 🌐 Public app down | ⛔ No support provided |
| 🏠 Local deployment issues | 📖 Follow [troubleshooting guide](local_deployment.md#troubleshooting) first |
| 🐛 Tool works but has problems | ✅ Interactive Help Tool → OR → ✅ FAQ → ✅ SRTM30 → ✅ Manual checklist → 💬 Discord/🐛 GitHub |
| 🗺️ Non-SRTM30 DTM issues | 👤 Contact DTM provider author at [PyDTMDL](https://github.com/iwatkot/pydtmdl) |ough troubleshooting step-by-step
- 📋 Help you fill out all required information
- 📄 Generate a shareable markdown file for support requests
- 🎯 Ensure you include all necessary details

**If the interactive tool doesn't solve your issue, it will prepare everything you need for manual support below.**

---

## Manual Support Process

If you prefer manual support or the interactive tool isn't available, follow the decision tree below step by step.

## 🚀 Step 1: Which version are you using?

<table>
<tr>
<td align="center" width="50%">

### 🌐 Public App
**https://maps4fs.xyz/**

[👉 Go to Step 2A](#step-2a-public-app---is-the-tool-working)

</td>
<td align="center" width="50%">

### 🏠 Local Deployment
**Docker/Python on your machine**

[👉 Go to Step 2B](#step-2b-local-deployment---is-the-tool-working)

</td>
</tr>
</table>

## Step 2A: Public App - Is the tool working?

<table>
<tr>
<td align="center" width="50%">

### ✅ YES
**Tool loads and responds**

[👉 Go to Step 3](#step-3-tool-works-but-has-issues)

</td>
<td align="center" width="50%">

### ❌ NO
**Tool is down/not loading**

⛔ **STOP HERE**

I do not accept any reports or questions related to the public app when it's not working. The public app is provided as-is without support guarantees.

</td>
</tr>
</table>

## Step 2B: Local Deployment - Is the tool working?

<table>
<tr>
<td align="center" width="50%">

### ✅ YES
**Tool loads and responds**

[👉 Go to Step 3](#step-3-tool-works-but-has-issues)

</td>
<td align="center" width="50%">

### ❌ NO
**Tool won't start/deploy**

📋 **REQUIRED: Follow troubleshooting first**

**Before asking for help, you MUST:**
1. ✅ Read the [Local Deployment Troubleshooting](local_deployment.md#troubleshooting)
2. ✅ Complete ALL troubleshooting steps
3. ✅ Include ALL outputs in your help request

</td>
</tr>
</table>

## Step 3: Tool works but has issues

> Tool loads but crashes during generation or produces unexpected results

### 📚 Have you checked the FAQ?

<table>
<tr>
<td align="center" width="50%">

### ✅ YES
**I've read the FAQ**

[👉 Continue to DTM Check](#dtm-provider-check)

</td>
<td align="center" width="50%">

### ❌ NO
**Haven't read it yet**

**📖 Read the [FAQ](FAQ.md) first**

Your issue might already be solved there!

</td>
</tr>
</table>

### 🗺️ DTM Provider Check

**Which DTM provider are you using?**

<table>
<tr>
<td align="center" width="50%">

### ✅ SRTM30 Provider
**The default/supported provider**

[👉 Go to Pre-submission Checklist](#step-4-pre-submission-checklist)

</td>
<td align="center" width="50%">

### ❌ Other DTM Provider
**Any provider except SRTM30**

⛔ **STOP HERE**

**I only support SRTM30 DTM provider.** 

For other DTM providers:
1. 🔗 Visit [PyDTMDL repository](https://github.com/iwatkot/pydtmdl)
2. 👤 Find the author of your DTM provider  
3. 📧 Contact them directly

**I do not provide help or accept reports for non-SRTM30 DTM providers.**

</td>
</tr>
</table>

## Step 4: Pre-submission Checklist

**Before submitting your issue, you MUST confirm ALL of the following:**

### ✅ Knowledge Check
- [ ] 📚 I have read the [FAQ](FAQ.md)
- [ ] 🗺️ I understand that map data comes from [OpenStreetMap](https://www.openstreetmap.org/)
- [ ] 🔍 I have verified that the required data exists on OpenStreetMap for my area
- [ ] 🎨 I understand what a [texture schema](texture_schema.md) is
- [ ] 🏷️ I have verified that my texture schema contains the OSM tags for the objects I'm missing *(if texture-related)*

### 🎯 Ready to Submit?

<table>
<tr>
<td align="center" width="50%">

### ✅ All Confirmed
**I've checked everything above**

[👉 Go to Step 5: Information Checklist](#step-5-information-checklist)

</td>
<td align="center" width="50%">

### ❌ Not Ready
**Still need to check some items**

⬆️ **Go back and complete the missing items**

This helps ensure you get the best possible help.

</td>
</tr>
</table>

## Step 5: Information Checklist

**Before contacting support, prepare the following information:**

### 📍 Basic Information
- [ ] **Map coordinates** (latitude, longitude) - *Example: 45.2841, 20.2370*
- [ ] **Map size** - *Example: 4x4 km*
- [ ] **Game version** - *FS22 or FS25*
- [ ] **Maps4FS version** - *Check in app footer or about section*

### 📁 Required Files
Gather these files from your map generation:

- [ ] **`generation_info.json`** - *Contains technical details about your map*
- [ ] **`main_settings.json`** - *Main configuration settings*
- [ ] **`generation_settings.json`** - *Your map generation settings*
- [ ] **Error logs** (if available) - *Any error messages or crash logs*
- [ ] **Screenshots** of the issue - *Show what's wrong vs what's expected*

### 📝 Issue Description
Prepare answers to these questions:

- [ ] **What exactly is wrong?** - *Describe the specific issue*
- [ ] **What did you expect to happen?** - *What should the correct behavior be*
- [ ] **Steps to reproduce** - *How can someone else reproduce this issue*
- [ ] **When did it start happening?** - *Was it working before? What changed?*

### 🔍 Additional Details (if applicable)
- [ ] **Custom settings used** - *Any non-default settings you applied*
- [ ] **Custom OSM file** - *If you used a custom OpenStreetMap file*
- [ ] **Custom texture schema** - *If you modified the texture schema*
- [ ] **Specific objects missing** - *Which roads/buildings/fields are missing*

### 📞 Choose Your Support Channel

**💡 TIP: If you used the [Interactive Help Tool](#-interactive-help-tool-recommended), you already have a formatted markdown file ready to share!**

<table>
<tr>
<td align="center" width="50%">

### 💬 Discord (Recommended)
**For most users**

✅ **Pros:**
- Fast community help
- Easy to share files
- No GitHub account needed

[![Join Discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/Sj5QKKyE42)

**Post in #support channel with:**
- Your interactive help output (if available)
- Or your manual checklist information

</td>
<td align="center" width="50%">

### 🐛 GitHub Issues
**For technical users**

✅ **Pros:**
- Detailed issue tracking
- Better for complex bugs
- Public record for others

**Requirements:**
- GitHub account
- Familiar with issue templates

🐛 **[Create GitHub Issue](https://github.com/iwatkot/maps4fs/issues/new/choose)**

**Paste your interactive help output or manual information**

</td>
</tr>
</table>

### 📋 Final Checklist
Before contacting support, confirm:

- [ ] ✅ I have ALL the information from the checklists above
- [ ] 📁 I have prepared all required files
- [ ] 📝 I can clearly describe my issue
- [ ] 🎯 I know which support channel to use

**Ready to get help!** 🚀

## 📋 Quick Reference Guide

| 🎯 Scenario | 🔄 Action |
|-------------|-----------|
| 🌐 Public app down | ⛔ No support provided |
| 🏠 Local deployment issues | 📖 Follow [troubleshooting guide](local_deployment.md#troubleshooting) first |
| 🐛 Tool works but has problems | ✅ FAQ → ✅ SRTM30 → ✅ Checklist → � Gather info → 💬 Discord/🐛 GitHub |
| 🗺️ Non-SRTM30 DTM issues | 👤 Contact DTM provider author at [PyDTMDL](https://github.com/iwatkot/pydtmdl) |

---
