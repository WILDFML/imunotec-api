# Imunotec Estoque

## Procedimentos de laboratório

A seção **Procedimentos** segue o mesmo fluxo do caderno de reuniões: os
protocolos são escritos em Quarto (`.qmd`), renderizados como HTML e lidos do
repositório configurado em `MEETINGS_REPOSITORY`. Salve cada fonte na pasta
`procedimentos` deste repositório. O workflow do GitHub Actions gera o HTML
automaticamente quando um `.qmd` é alterado. Imagens usadas nos documentos
devem ficar nessa pasta ou em subpastas dela.

Use [modelo-procedimento.qmd](./modelos/modelo-procedimento.qmd) como ponto de
partida e salve cada protocolo com um nome próprio, por exemplo
`procedimentos/POP-preparo-de-amostras.qmd`. O YAML do modelo inclui categoria,
tags, versão, responsável e datas de revisão, além de nomes de reagentes como
aparecem no estoque. Esses dados alimentam os filtros, os alertas de revisão e
os vínculos aos lotes. A busca também consulta o conteúdo do protocolo.

Cada usuário pode favoritar procedimentos; os favoritos são salvos na API e
permanecem associados à conta. Para habilitar essa função, publique também a
atualização da API antes de publicar o app Streamlit. O app reutiliza
`MEETINGS_GITHUB_TOKEN` para ler os arquivos QMD e HTML do repositório privado.

O workflow de renderização precisa de permissão de escrita em Actions >
General > Workflow permissions para publicar os HTML gerados. Se a organização
ou a proteção da branch bloquear esse tipo de commit, ajuste a política do
repositório antes de depender da renderização automática.

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
