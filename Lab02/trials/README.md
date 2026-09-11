# Código final dos trials

Esta pasta preservará o estado final do código produzido em cada tentativa.

Organização gerada por `scripts/prepare_trial.py`:

```text
trials/
└── PXX-KXX-tratamento/
    ├── README.md
    ├── src/
    ├── trial-config.json
    └── treatment-verification.json
```

Use `ai` ou `manual` como tratamento. Os resultados do cronômetro ficam em
`data/raw/trials/<trial_id>/`; esta pasta preserva o código final e as
verificações de preparação. O diretório deve corresponder ao `trial_id`, à
Issue e ao commit registrados no dataset. Não inclua aqui conversas, tokens,
credenciais ou informações pessoais.
