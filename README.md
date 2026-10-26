# Imunotec Estoque

## Procedimentos de laboratório

A seção **Procedimentos** oferece uma biblioteca compartilhada entre os
utilizadores autenticados. Cada protocolo pode incluir nome, categoria,
objetivo, materiais e equipamentos, passo a passo e cuidados de segurança.
Qualquer utilizador autenticado pode cadastrar, consultar, editar e excluir
procedimentos; a data de revisão é atualizada automaticamente ao salvar
alterações.

Os procedimentos são armazenados no banco de estoque, junto dos lotes. A tabela
é criada automaticamente na inicialização da API. Para disponibilizar o
recurso, publique as alterações da API e do app Streamlit; a versão do app
depende das novas rotas `/procedimentos/` da API.

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
