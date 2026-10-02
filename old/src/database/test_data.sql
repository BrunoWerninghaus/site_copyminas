-- Script para popular tabelas com dados de teste
-- IMPORTANTE: Execute este script APENAS para teste!

-- Inserir usuário admin (senha: admin123)
INSERT INTO USERS (name, email, password, is_admin) VALUES 
('Administrador', 'admin@test.com', 'scrypt:32768:8:1$SvpH85mUpri61DvM$bd054cd626501f9cf8bd29c56a2510a28874b25994a67c1cc25701bf950b7fed7be258b72b9b7b6ff4c38fabc81835825d4465fbdde36cb40e98e101708f45b9', TRUE);

-- Inserir usuário comum (senha: user123)
INSERT INTO USERS (name, email, password, is_admin) VALUES 
('Usuário Teste', 'user@test.com', 'scrypt:32768:8:1$ZAxg7mjfhhinec0p$9ea4114fc6f1ce56233944ae6097168225e98e2639241c1a2828df50132dd8708f561a0cae9dbd21b7302b8db4fc650239ce03e1ac9ca7757dadc1942e37d281', FALSE);

-- Inserir alguns equipamentos
INSERT INTO EQUIPMENTS (name, description, user_id) VALUES 
('Servidor 1', 'Servidor principal de produção', 2),
('Impressora Rede', 'Impressora da rede corporativa', 2),
('Computador 3', 'Desktop de trabalho', 2);
