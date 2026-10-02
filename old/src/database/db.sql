-- Remover tabelas antigas (se existirem)
-- Drop dependents first to avoid foreign-key constraint errors
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS maintenance_requests;
DROP TABLE IF EXISTS user_equipments;
DROP TABLE IF EXISTS equipments;
DROP TABLE IF EXISTS users;

-- Tabela de usuários com senhas criptografadas
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de equipamentos GENÉRICOS da empresa (sem usuário específico)
CREATE TABLE equipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name)
);

-- Tabela para relacionar usuários com equipamentos + tipo (aluguel ou pessoal)
CREATE TABLE user_equipments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    equipment_id INT NOT NULL,
    type ENUM('rental', 'personal') NOT NULL DEFAULT 'personal',
    serial_number VARCHAR(100),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_equipment_id (equipment_id),
    INDEX idx_type (type)
);

-- Tabela de requisições de manutenção
CREATE TABLE maintenance_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    equipment_id INT NOT NULL,
    description TEXT NOT NULL,
    status ENUM('pendente', 'em_andamento', 'concluida', 'cancelada') DEFAULT 'pendente',
    priority ENUM('baixa', 'media', 'alta') DEFAULT 'media',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (equipment_id) REFERENCES equipments(id) ON DELETE CASCADE
);

-- Tabela de logs de auditoria para segurança
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
