This project now includes a small modern UI enhancement:

- Static assets:
  - `projects/static/projects/app.css` — theme variables, responsive styles, animated cards, loading overlay.
  - `projects/static/projects/app.js` — theme toggle, stat number animations, loading control.

How to test locally:
1. Ensure `DEBUG = True` in Django `settings.py` (or staticfiles configured).
2. Run the development server:

```bash
python manage.py runserver
```

3. Open the app in browser and try the theme toggle in the top-right of the navbar. Stats animate on load.

If you deploy with whitenoise or collectstatic, run `python manage.py collectstatic` as usual.