# Contributing

Contributions that improve reproducibility, documentation, tests, or safe runtime
behavior are welcome.

Before opening a pull request:

1. do not add audio, transcripts, competition test files, predictions, model
   weights, KenLM binaries, credentials, or private Drive artifacts;
2. preserve upstream attribution and licenses;
3. clear all notebook outputs and execution counts;
4. describe whether a result is measured, inferred, or proposed;
5. run `python scripts/validate_release.py`;
6. include the exact command or notebook cells used for validation.

Do not rewrite or move historical score claims without explaining how compliance
was evaluated. New decoder routes require a tune/audit split and rollback rule,
not only a lower tuning WER.

