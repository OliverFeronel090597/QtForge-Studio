# QtForge Studio

![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.14%2B-blue)
![Qt](https://img.shields.io/badge/Qt-PyQt6%20%7C%20PySide6-brightgreen)

**QtForge Studio** is an open-source developer tool for **hosting, testing, and hot-reloading Qt widgets** in a controlled runtime environment.

It allows developers to load renderers dynamically, run them inside either `QMainWindow` or `QWidget`, and validate UI behavior **without restarting the application**.

---

## ✨ Features

* 🔁 Live renderer updates (hot-reload friendly)
* 🧩 Host-agnostic architecture (`QMainWindow` ↔ `QWidget`)
* 📦 Single renderer, multiple host testing
* 📊 Supports complex widgets (charts, layouts, controls)
* 🧪 Ideal for UI prototyping and renderer isolation
* 🪶 Lightweight and framework-agnostic

---

## 🎯 Use Cases

* Rapid Qt UI prototyping
* Renderer / widget isolation testing
* Plugin-style UI development
* Hot-reload workflows for Qt projects
* Internal tools and R&D environments

---

## 🛠 Tech Stack

* Python 3.11+
* PyQt6 / PySide6
* Qt Charts (optional)
* MIT License

---

## 📦 Installation

```bash
pip install PyQt6 PyQt6-Charts
```

Clone the repository:

```bash
git clone https://github.com/OliverFeronel090597/special-carnival.git
cd QtForge\ Studio
```

---

## ▶️ Usage

Run the test harness:

```bash
python main.py
```

Toggle between `QMainWindow` and `QWidget` hosts by changing a single flag in the code.

---

## 🧠 Design Philosophy

QtForge Studio treats **renderers as pure widgets** and **windows as replaceable shells**.

If a widget cannot run outside a `QMainWindow`, it is not a renderer — it is a design flaw.

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2025 Oliver Feronel (Queen)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## ⚖️ Trademark Notice

Qt is a registered trademark of **The Qt Company**.

QtForge Studio is **not affiliated with or endorsed by The Qt Company**.
