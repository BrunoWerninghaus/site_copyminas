# 🔐 Credenciais de Teste

## Admin
- **Email**: `admin@copyminas.com`
- **Senha**: `AdminPass123!`
- **Acesso**: Painel administrativo, criação de equipamentos, atribuição de equipamentos, visualização de todas as requisições

---

## Clientes

### 1. João Silva
- **Email**: `joao@copyminas.com`
- **Senha**: `Password123!`
- **Equipamentos Atribuídos**: 3 equipamentos rental
- **Status**: Ativo

### 2. Maria Santos
- **Email**: `maria@copyminas.com`
- **Senha**: `Password123!`
- **Equipamentos Atribuídos**: 2 equipamentos rental
- **Status**: Ativo

### 3. Pedro Oliveira
- **Email**: `pedro@copyminas.com`
- **Senha**: `Password123!`
- **Equipamentos Atribuídos**: 2 equipamentos rental
- **Status**: Ativo

### 4. Ana Costa
- **Email**: `ana@copyminas.com`
- **Senha**: `Password123!`
- **Equipamentos Atribuídos**: 0 equipamentos (para testar atribuição)
- **Status**: Ativo

---

## 📋 Casos de Teste Recomendados

### Dashboard
- [ ] Login como admin → Deve ver TODOS os equipamentos e TODAS as requisições
- [ ] Login como João → Deve ver apenas seus 3 equipamentos e suas requisições
- [ ] Login como Ana → Deve ver 0 equipamentos (nenhum atribuído)

### Painel de Manutenção
- [ ] Admin: Criar requisição para qualquer usuário com qualquer equipamento genérico
- [ ] João: Criar requisição apenas para seus equipamentos rental
- [ ] Ana: Não conseguir criar (sem equipamentos)

### Perfil do Usuário (Admin)
- [ ] Atribuir novo equipamento para Ana com tipo "rental"
- [ ] Verificar que Ana pode criar requisição com o novo equipamento

### Equipamentos
- [ ] Admin: Criar novo equipamento genérico
- [ ] Verificar que o novo equipamento aparece em todas as dropdowns (admin)

---

## 🔄 Fluxo de Teste Recomendado

1. **Login Admin** → Dashboard
2. **Verificar**: Todos os equipamentos genéricos visíveis
3. **Verificar**: Todas as requisições com username visível
4. **Criar Requisição**: Para João em algum equipamento
5. **Logout** → **Login João**
6. **Dashboard**: Deve ver apenas seus 3 equipamentos
7. **Verificar**: Sua nova requisição aparece
8. **Painel Manutenção**: Tentar criar em equipamento que não possui (deve bloquear)

---

## 📝 Notas

- Senhas são criptografadas em pbkdf2:sha256
- Admin é identificado por flag `is_admin = 1` na tabela users
- Equipamentos "rental" são os atribuídos aos usuários
- Equipamentos "personal" são para uso administrativo interno
- Todos os dados são resetáveis via `seed_db.py`

---

**Última Atualização**: 28/02/2026
**Status**: ✅ Sistema pronto para testes
