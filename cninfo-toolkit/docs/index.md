# cninfo-toolkit Documentation

Welcome to the **cninfo-toolkit** documentation — a free, open-source Python
toolkit for fetching A-share company announcements from
[cninfo.com.cn](http://www.cninfo.com.cn/) (巨潮资讯网).

## What is cninfo-toolkit?

cninfo-toolkit is a Python package that provides direct access to **publicly
available** A-share company announcement data from cninfo.com.cn. It is:

- 🆓 **Free** — No API keys, no authentication, no rate-limit fees
- 🐍 **Pythonic** — Both CLI and Python API
- 🔄 **Cross-platform** — Works on macOS, Linux, Windows
- 🧪 **Type-safe** — Full type hints with mypy strict mode
- 📦 **Production-grade** — Rate limiting, retries, PDF integrity validation

## When to use it

Use cninfo-toolkit when you need to:

- 📊 Build investment research tools for A-share stocks
- 🤖 Train ML models on Chinese financial announcements
- 📰 Track specific companies' disclosures (e.g., for due diligence)
- 🎓 Conduct academic research on Chinese capital markets
- 🔍 Build compliance monitoring systems

## When NOT to use it

- ❌ To redistribute cninfo data in commercial products (review cninfo's terms)
- ❌ For high-frequency trading (use professional data vendors)
- ❌ For real-time data (cninfo-toolkit fetches T+1 data only)

## Next steps

- [Installation Guide](installation.md) — Get started in 5 minutes
- [Quickstart](quickstart.md) — See practical examples
- [API Reference](api.md) — Complete API documentation