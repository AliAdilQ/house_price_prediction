# Contributing

Thank you for helping improve House Price Prediction.

1. Fork [AliAdilQ/house_price_prediction](https://github.com/AliAdilQ/house_price_prediction).
2. Clone your fork and follow the README installation instructions.
3. Create a branch: `git switch -c feature/your-change`.
4. Keep Django views, ML services, and frontend code separated. Use the shared feature schema when changing inputs.
5. Add meaningful behavior tests for changed functionality. If the schema changes, generate migrations; if the training inputs change, regenerate the CSV and retrain the pipeline together.
6. Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test`.
7. Inspect affected pages on desktop and mobile. Update documentation and screenshots if needed.
8. Commit with a clear message, push your branch to your fork, and open a pull request explaining the change and its validation.

Never commit `.env`, your SQLite database, personal property data, or credentials. Use synthetic examples. Retain dependency licenses when updating vendored assets.
