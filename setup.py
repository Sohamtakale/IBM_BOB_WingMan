from setuptools import setup, find_packages

setup(
    name="reflex-loop",
    version="0.1.0",
    packages=["reflex_loop"],
    package_dir={"reflex_loop": "reflex-loop"},
    install_requires=[
        "pyaudio",
        "webrtcvad-wheels",
        "numpy",
        "deepgram-sdk",
        "python-dotenv",
        "google-generativeai",
        "groq"
    ],
    entry_points={
        "console_scripts": [
            "reflex-loop=reflex_loop.main:main",
        ]
    }
)
