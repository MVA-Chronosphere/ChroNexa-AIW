# Contributing to ChroNexa

Thank you for interest in contributing to ChroNexa! Here's how you can help.

## Code of Conduct

Be respectful and professional in all interactions.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Test your changes
6. Commit with clear messages: `git commit -m "Add feature description"`
7. Push to your branch: `git push origin feature/your-feature`
8. Open a Pull Request

## Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## Testing

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Format with Black: `black .`
- Lint with Flake8: `flake8 .`

### TypeScript/React
- Use Prettier for formatting
- Follow ESLint rules
- Use meaningful variable names
- Add JSDoc comments for complex functions

## Commit Messages

```
feat: Add new feature
fix: Fix a bug
docs: Update documentation
style: Code style changes
refactor: Code refactoring
test: Add tests
chore: Maintenance tasks
```

## Pull Request Process

1. Update relevant documentation
2. Add tests for new functionality
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Areas for Contribution

- [ ] Additional LLM providers
- [ ] More avatar customization options
- [ ] Enhanced lip-sync accuracy
- [ ] Improved UI/UX
- [ ] Documentation improvements
- [ ] Bug fixes
- [ ] Performance optimizations
- [ ] Testing

## Questions?

Open an issue or discussion thread in the repository.

---

Thank you for contributing to ChroNexa!
