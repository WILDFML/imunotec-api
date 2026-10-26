# Imunotec Estoque

## Procedimentos de laboratório

A seção **Procedimentos** segue o mesmo fluxo do caderno de reuniões: os
protocolos são escritos em Quarto (`.qmd`), renderizados como HTML e lidos do
repositório configurado em `MEETINGS_REPOSITORY`. Coloque os arquivos-fonte e
os HTML publicados na pasta `procedimentos` desse repositório. Imagens usadas
nos documentos devem ficar nessa pasta ou em subpastas dela.

Use [modelo-procedimento.qmd](./modelos/modelo-procedimento.qmd) como ponto de
partida e salve cada protocolo com um nome próprio, por exemplo
`procedimentos/POP-preparo-de-amostras.qmd`. Publique também o HTML
correspondente; o nome do arquivo HTML aparece como título no app. Não é
necessário configurar novas variáveis ou publicar novas rotas na API: a
biblioteca reutiliza `MEETINGS_GITHUB_TOKEN` e a integração existente do
caderno de reuniões. Após publicar os HTML no repositório, eles aparecem na
seção **Procedimentos** do app.

## Recuperação de senha

A recuperação envia um link por e-mail. Configure estas variáveis no ambiente
da API (por exemplo, nas configurações do serviço no Render):

```text
SMTP_HOST=smtp.seuprovedor.com
SMTP_PORT=587
SMTP_USERNAME=usuario
SMTP_PASSWORD=senha-de-aplicativo
SMTP_FROM_EMAIL=Imunotec <nao-responda@seudominio.org>
FRONTEND_URL=https://seu-app.streamlit.app
```

Use a porta `587` com STARTTLS ou a porta `465` com SSL implícito. `FRONTEND_URL`
deve ser a URL pública do app Streamlit. As credenciais SMTP devem permanecer
somente nas variáveis de ambiente do serviço; não as inclua no repositório.

Os links expiram em 30 minutos e podem ser usados uma única vez. Novas
solicitações para a mesma conta são limitadas a uma por minuto. A tabela de
tokens é criada automaticamente junto das tabelas de autenticação.
