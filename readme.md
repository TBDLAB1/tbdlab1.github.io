# Research Group Static Website

This is a static website for a research group, hosted as GitHub Pages.

The website rebuilds itself every 30 minutes from a Google Sheets document via a scheduled GitHub Actions job, so editing the spreadsheet is enough to update the site.

![Builder](https://github.com/TBDLAB1/tbdlab1.github.io/actions/workflows/builder.yml/badge.svg)

## How does this website work?

The [Builder workflow](.github/workflows/builder.yml) runs the Python builder in *[builder](builder)*, which downloads the contents from Google Sheets and renders the static site into the *docs* folder **on the runner**. It then deploys that folder straight to GitHub Pages as an artifact — **nothing is committed back to the repository.**

The workflow runs:
- every 30 minutes (scheduled),
- on every push to *master*, and
- manually via the **Run workflow** button on the [Actions](https://github.com/TBDLAB1/tbdlab1.github.io/actions/workflows/builder.yml) page.

> The *docs* folder is a build artifact — it is regenerated on every run and you do **not** need to commit it. To update the site, edit the Google Sheets document (or push a code change), then let the workflow run.

## How to upload static files to this website

If you need to upload images or any other static files for use on the website, put them in the *[assets](assets)* folder. Everything there is copied into the built site's *assets* folder at build time.

## How to create your own website from this

1. Fork this repository to your account.

1. Configure the repository to publish GitHub Pages using **GitHub Actions** as the source: *Settings → Pages → Build and deployment → Source → **GitHub Actions***. (This project deploys the built site as an artifact, so do **not** use "Deploy from a branch".)

1. Configure a custom domain for your website if you need to. Read [this document](https://docs.github.com/en/free-pro-team@latest/github/working-with-github-pages/configuring-a-custom-domain-for-your-github-pages-site) if you need help.

1. Create a Google Sheets document for your contents and add its URL as the `DATA_URL` secret (see below).

1. Get a Google API key and add it as the `API_KEY` secret (see below).

1. Voilà! Once the workflow runs, your website is live on GitHub Pages.

The spreadsheet URL and API key are read from the `DATA_URL` and `API_KEY` **repository secrets** (Settings → Secrets and variables → Actions), so they are never committed to the repo. For a local build, pass them as environment variables:

```bash
INPUT_API_KEY=<key> INPUT_DATA_URL=<sheet-url> python3 build.py
```

### Create a data source document

The site's contents come from a Google Sheets document, whose URL is stored in the `DATA_URL` secret.

An example document is available at [here](https://docs.google.com/spreadsheets/d/1EDLlUuY2Ia5MKNbCTOftxxSxBaK3C9pRFOIUvMY30eY/edit?usp=sharing).

To create your own document, follow the instructions below. 

1. Use [this link](https://docs.google.com/spreadsheets/d/1EDLlUuY2Ia5MKNbCTOftxxSxBaK3C9pRFOIUvMY30eY/copy#gid=1676718498) to make a copy of the example Sheets document. 

1. Set your document's sharing settings as: *Public on the web - Anyone on the Internet can find and view*. Read [this document](https://support.google.com/docs/answer/183965?co=GENIE.Platform%3DDesktop&hl=en) if you need help.

1. Add the document URL as the `DATA_URL` secret (Settings → Secrets and variables → Actions → New repository secret).

### Get a Google API Key

The builder needs a Google API key to read the Google Sheets document. Add it as the `API_KEY` secret.

1. Create an API key in the [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and enable the **Google Sheets API** for its project.
1. Set **Application restrictions → None** (no HTTP referrer restriction). The builder calls the API server-side with no referrer, so a referrer-restricted key fails with `403`.
1. Add the key as the `API_KEY` secret.

## Configuring the navigation menu

The top navigation bar is driven by a **`Menu`** tab in the Google Sheets document (columns `Menu`, `Submenu`, `URL`, with data starting at row 2). Each row is one entry:

| Menu | Submenu | URL |
| --- | --- | --- |
| Home | | / |
| Members | PI | /members/pi |
| Members | Students | /members/students |
| Research | | /research |
| Contact | | /contact |

- Leave **Submenu** empty for a normal, one-level link (e.g. *Home*, *Research*).
- Fill **Submenu** to turn that **Menu** label into a two-level dropdown; every row sharing the same **Menu** value becomes an item in that dropdown (e.g. *Members → PI / Students*).

If there is no `Menu` tab, the site falls back to the default menu (Home, Members, Research, Links, Contact).

## Creating separate member pages

In addition to the combined */members* page (built from the `Members` tab), you can publish extra member pages, each managed in its own tab:

1. Add a tab named **`Members - <Name>`** (e.g. `Members - PI`, `Members - Students`) using the **same columns as the `Members` tab**.
1. It is automatically published at **`/members/<name>`**, where `<name>` is lower-cased with spaces turned into hyphens (`Members - PI` → `/members/pi`).
1. Link to it from the `Menu` tab (see above).

Within each page, column A is still the section heading, so a single page can hold several groups (e.g. a *Students* page with *Ph.D. Student*, *M.S. Student*, … sections).

## Gallery (photo albums from Google Drive)

The `/gallery` page shows photo albums as slideshows. Each album is one row in a **`Gallery`** tab (columns `Title`, `Drive folder`, `Description`, from row 2):

| Title | Drive folder | Description (Markdown) |
| --- | --- | --- |
| Jeju Conference | https://drive.google.com/drive/folders/FOLDER_ID | ## We had a great time … |

- **Photos live in Google Drive.** Put the album's photos in a Drive folder, share it *Anyone with the link – Viewer*, and paste the folder link in column B. **Every image in that folder becomes a slide** (ordered by file name).
- Column A is the album title; column C is an optional Markdown description.
- Add an album = add a row; add photos = drop files into the Drive folder. No per-photo editing.
- Requirements: the `API_KEY` must have the **Google Drive API** enabled (in addition to Sheets), and the folder must be publicly viewable.
- Link the page from the `Menu` tab (`Gallery → /gallery`).

## Acknowledgements

This work was supported and funded by [JinYeong Bak](https://nosyu.github.io/). The developer of this repo is [Jeongmin Byun](https://jmbyun.github.io/).

## Tips
- How to do line breaks in markdown
  - Two spaces at the end of the line (recommended, https://stackoverflow.com/a/33191810)
  - One empty line between lines
  - Reference: https://gist.github.com/shaunlebron/746476e6e7a4d698b373
- How to update the webpage
  - Edit the Google Sheets document (contents) or the *assets* folder (static files), then wait up to 30 minutes, **or**
  - Go to the [Actions](https://github.com/TBDLAB1/tbdlab1.github.io/actions/workflows/builder.yml) page and click the `Run workflow` button to update immediately
