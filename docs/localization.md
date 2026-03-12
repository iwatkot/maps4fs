# Localization

**Community-Driven UI Translations for Maps4FS**

The Maps4FS interface supports multiple languages through a community-driven localization system. Anyone can contribute by adding a new language or improving an existing translation — no coding experience required.

## 🌐 Locale Repository

All translations are maintained in a dedicated public repository:

**[https://github.com/iwatkot/maps4fslocale](https://github.com/iwatkot/maps4fslocale)**

The repository contains locale files for every supported language and includes full instructions for contributors. When a translation is added or updated in the repository, it is automatically reflected in both the **Windows App** and the **Docker** version of Maps4FS.

## 📁 How It Works

Locale files live under the `languages/` directory of the repository. Each file is named using the language's [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) code (e.g. `en.yml` for English, `sr.yml` for Serbian) and follows a simple YAML structure:

```yaml
meta:
  code: en
  full: English
  localized: English

some_section:
  label: Some Label
  tooltip: Some tooltip text
```

The `meta` block identifies the language. The rest of the file maps UI keys to their translated strings.

## 🤝 How to Contribute

1. **Fork** the [maps4fslocale](https://github.com/iwatkot/maps4fslocale) repository.
2. Browse the `languages/` directory to see what already exists.
3. To **add a new language** — copy `en.yml`, rename it to your language code (e.g. `de.yml`), and translate the values.
4. To **improve an existing translation** — edit the corresponding file directly.
5. Open a **Pull Request** with your changes.

Refer to the repository's README for the full contribution guidelines and any additional requirements.

## 📲 Where Translations Appear

Accepted translations are picked up automatically by both deployment methods:

- **Windows App** — see [Windows App](windows_app.md) for installation details.
- **Docker** — see [Local Deployment (Docker)](local_deployment.md) for setup instructions.

The language can be selected inside the application's interface once a locale file for that language is available.




