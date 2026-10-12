# Caderno de reuniões

O app procura arquivos HTML no diretório `atas/` de um repositório GitHub
privado. Mantenha os arquivos `.qmd` e os HTML renderizados nesse repositório,
não neste repositório público do app.

## Publicar uma reunião

1. Crie um repositório privado para as atas.
2. Copie `modelo-ata.qmd` para `atas/` nesse repositório.
3. Crie um arquivo com nome começando pela data, por exemplo
   `atas/2026-10-12-reuniao.qmd`, e preencha a ata.
4. No terminal, dentro do repositório privado, renderize o arquivo:

   ```text
   quarto render atas/2026-10-12-reuniao.qmd
   ```

5. Revise e envie para o repositório privado tanto o `.qmd` quanto o `.html`
   gerado. O app apresenta os arquivos `.html` que encontrar em `atas/`.

## Conectar o app ao repositório

Crie um token do GitHub com acesso somente de leitura ao conteúdo do repositório
privado. Nas configurações do app no Streamlit Community Cloud, adicione estes
secrets e salve:

```toml
MEETINGS_REPOSITORY = "organizacao/repositorio-privado"
MEETINGS_GITHUB_TOKEN = "token-de-leitura"
```

Para desenvolvimento local, as mesmas configurações podem ser definidas como
variáveis de ambiente. Nunca inclua o token nos arquivos versionados.

O login do app restringe a visualização pelo Streamlit, mas não substitui a
privacidade do repositório de origem. Não publique atas reais neste repositório
público nem inclua dados pessoais, clínicos ou confidenciais sem autorização.
