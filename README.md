# The Daily Twenty

Ten news stories from around the world, ten from India, every morning.

Live at **https://thedailytwenty.netlify.app**

## How it works

Each morning a scheduled task researches the day's news, writes an edition file
into `data/`, and runs the generator. Netlify republishes automatically when the
new pages land here.

    data/YYYY-MM-DD.json   one file per edition, the source of truth
    build.py               turns those into the site
    public/                generated pages, served by Netlify

## Rebuilding by hand

    python3 build.py

That regenerates `public/` from every file in `data/` — the homepage shows the
newest edition, and the archive lists them all.

## Adding an edition

Drop a new `data/YYYY-MM-DD.json` in place with ten `world` items and ten
`india` items, each with a `tag`, `headline`, `body`, `source_name` and
`source_url`, then rebuild.
