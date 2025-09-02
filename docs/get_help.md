# Getting Help with Maps4FS

This guide will help you get the right support for your Maps4FS issue. Please follow the decision tree below step by step.

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

---

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

---

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

---

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

---

## Step 4: Pre-submission Checklist

**Before submitting your issue, you MUST confirm ALL of the following:**

### ✅ Knowledge Check
- [ ] 📚 I have read the [FAQ](FAQ.md)
- [ ] 🗺️ I understand that map data comes from [OpenStreetMap](https://www.openstreetmap.org/)
- [ ] 🔍 I have verified that the required data exists on OpenStreetMap for my area
- [ ] 🎨 I understand what a [texture schema](../README.md#texture-schema) is
- [ ] 🏷️ I have verified that my texture schema contains the OSM tags for the objects I'm missing *(if texture-related)*

### 🎯 Ready to Submit?

<table>
<tr>
<td align="center" width="50%">

### ✅ All Confirmed
**I've checked everything above**

🐛 **[Submit your issue here](https://github.com/iwatkot/maps4fs/issues/new/choose)**

Use the issue template and provide all requested details.

</td>
<td align="center" width="50%">

### ❌ Not Ready
**Still need to check some items**

⬆️ **Go back and complete the missing items**

This helps ensure you get the best possible help.

</td>
</tr>
</table>

---

## 📋 Quick Reference Guide

| 🎯 Scenario | 🔄 Action |
|-------------|-----------|
| 🌐 Public app down | ⛔ No support provided |
| 🏠 Local deployment issues | 📖 Follow [troubleshooting guide](local_deployment.md#troubleshooting) first |
| 🐛 Tool works but has problems | ✅ FAQ → ✅ SRTM30 → ✅ Checklist → 🐛 Submit issue |
| 🗺️ Non-SRTM30 DTM issues | 👤 Contact DTM provider author at [PyDTMDL](https://github.com/iwatkot/pydtmdl) |

---

## 💬 Community Support

<div align="center">

**Need immediate help? Join our community!**

[![Join Discord](https://img.shields.io/badge/join-discord-blue)](https://discord.gg/Sj5QKKyE42)

*Please follow this guide before asking questions in Discord*

</div>

---

<div align="center">
<i>📝 Following this guide helps everyone get better, faster support!</i>
</div>
