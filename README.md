# Imunotec Estoque

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
