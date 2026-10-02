# Sistema de Gerenciamento de Manutenção de Equipamentos

## Configuração e Segurança

### 1. Estrutura do Banco de Dados
O banco de dados foi atualizado com:
- **USERS**: Tabela de usuários com senhas criptografadas e campo `is_admin`
- **EQUIPMENTS**: Tabela de equipamentos associados aos usuários
- **MAINTENANCE_REQUESTS**: Tabela de requisições de manutenção

### 2. Segurança de Senhas
Todas as senhas são criptografadas usando `werkzeug.security` com PBKDF2-SHA256:
- As senhas são **nunca** armazenadas em texto plano
- As senhas são hasheadas com salt aleatório
- A validação de login usa `check_password()` para comparação segura

### 3. Dados de Teste
Para testar o sistema:

```bash
# 1. Gerar hashes de senha
python generate_password_hash.py

# 2. Copiar os hashes gerados para src/database/test_data.sql

# 3. Executar o script SQL no banco de dados
mysql main_bd < src/database/db.sql
mysql main_bd < src/database/test_data.sql
```

### 4. Credenciais de Teste
Após executar os scripts:
- **Admin**: usuário: `Administrador` | senha: `admin123`
- **Usuário**: usuário: `Usuário Teste` | senha: `user123`

### 5. Funcionalidades

#### Usuário Comum
- Fazer login
- Ver painel de usuário
- Solicitar manutenção de equipamentos
- Ver histórico de requisições

#### Admin
- Fazer login
- Ver todas as requisições de manutenção
- Atualizar status das requisições (pendente → em andamento → concluída/cancelada)
- Ver usuários e equipamentos associados

### 6. Fluxo de Uso

**Usuário Cliente:**
1. Acessa `/login`
2. Insere credenciais
3. É redirecionado para `/dashboard`
4. Clica em "Requisições de Manutenção"
5. Cria nova requisição selecionando equipamento
6. Admin verá a requisição em `/admin`

**Admin:**
1. Acessa `/login`
2. Insere credenciais de admin
3. É automaticamente redirecionado para `/admin`
4. Visualiza todas as requisições
5. Atualiza status das requisições

### 7. Estrutura de Diretórios
```
src/
├── controller/
│   ├── login_controller.py (com criptografia)
│   ├── admin_controller.py
│   ├── maintenance_controller.py
│   └── ...
├── templates/
│   ├── login.html
│   ├── admin.html
│   ├── maintenance.html
│   └── ...
├── utils/
│   └── password_utils.py (funções de hash)
├── database/
│   ├── db.sql (schema atualizado)
│   └── test_data.sql (dados de teste)
└── app.py (configurado com novas rotas)
```

### 8. Notas de Segurança
- ⚠️ Mude a `app.secret_key` em `src/app.py` para uma chave aleatória e segura
- ⚠️ Altere as credenciais do banco de dados (senha do root)
- ⚠️ Use variáveis de ambiente para credenciais sensíveis em produção
- ⚠️ Implemente validação de entrada para prevenir SQL injection
- ⚠️ Use HTTPS em produção

### 9. Próximas Melhorias
- [ ] Autenticação com tokens (JWT)
- [ ] Rate limiting para login
- [ ] Logs de auditoria
- [ ] Notificações por email
- [ ] Dashboard com gráficos
- [ ] Exportar relatórios
