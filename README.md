# Django PC Game Store (HTMX + Tailwind)

A clean, modern game store built with Django, HTMX, and Tailwind CSS. Supports a browsable catalog, a session cart, guest checkout, and email delivery of keys (console backend in dev).

## Quick Start

1. Create and activate a virtualenv
   - Windows (PowerShell): `python -m venv .venv && .venv\Scripts\Activate.ps1`
   - macOS/Linux: `python -m venv .venv && source .venv/bin/activate`

2. Install dependencies
   - `pip install django`

3. Migrate and create a superuser
   - `python manage.py migrate`
   - `python manage.py createsuperuser`

4. Load sample data (optional)
   - `python manage.py loaddata store/fixtures/sample_games.json`

5. Run the server
   - `python manage.py runserver`

Open http://127.0.0.1:8000/ to view the store. Admin is at `/admin/`.

## Notes

- Tailwind is included via CDN for fast iteration. For production, swap to a proper Tailwind build.
- Email uses Django’s console backend in development. Configure SMTP in `gamestore/settings.py` for real delivery.
- Images are URL-based to avoid local file storage in this skeleton. You can switch `Game.image` to an `ImageField` later and configure media.
- HTMX enables in-page updates for filtering and cart operations without full page reloads.

## Models

- `Game`: title, price, original_price, category, image(URL), description.
- `Order` and `OrderItem`: guest checkout orders.
- `GameKey`: optional pool of keys per game. On checkout, available keys are assigned and emailed.

## Next Steps

- Add payment integration (Stripe/Paystack/etc.).
- Build a Tailwind pipeline (PostCSS) for production assets.
- Add inventory, stock visibility, and richer filters.

