"""Configure Kaggle + Hugging Face auth from the tokens Carter saved in kaggle.md.

Never prints a token. Writes:
  - %USERPROFILE%\\.kaggle\\access_token   (kaggle CLI >= 1.7 reads this automatically)
  - the huggingface_hub token cache         (same as `hf auth login`)
Then verifies both logins and prints only usernames.
"""
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTES = HERE / "kaggle.md"


def main() -> int:
    text = NOTES.read_text(encoding="utf-8", errors="ignore")
    kaggle_tok = re.search(r"\b(KGAT_[A-Za-z0-9]+)\b", text)
    hf_tok = re.search(r"\b(hf_[A-Za-z0-9]+)\b", text)
    if not kaggle_tok or not hf_tok:
        print("could not find both tokens in kaggle.md", file=sys.stderr)
        return 1

    kdir = Path.home() / ".kaggle"
    kdir.mkdir(exist_ok=True)
    (kdir / "access_token").write_text(kaggle_tok.group(1), encoding="utf-8")
    os.environ["KAGGLE_API_TOKEN"] = kaggle_tok.group(1)

    from huggingface_hub import login, whoami

    login(token=hf_tok.group(1), add_to_git_credential=False)
    print("HF user:", whoami()["name"])

    from kaggle.api.kaggle_api_extended import KaggleApi

    api = KaggleApi()
    api.authenticate()
    print("Kaggle user:", api.config_values.get("username"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
