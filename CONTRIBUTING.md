# Contributing to PhantomTrace

Thank you for your interest!

## How to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and commit: `git commit -m 'Add: my feature'`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Keep modules independent and self-contained

## Adding a New Module

1. Create `modules/my_module.py`
2. Implement a class with `run(target: str) -> Dict` and `display(data: Dict)` methods
3. Register it in `main.py` under `module_map` and the menu
