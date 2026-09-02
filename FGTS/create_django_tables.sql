-- Criar tabelas de sessão e autenticação do Django que faltam
CREATE TABLE IF NOT EXISTS django_session (
    session_key VARCHAR(40) PRIMARY KEY,
    session_data TEXT NOT NULL,
    expire_date TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_django_session_expire_date ON django_session(expire_date);

-- Criar tabela de content type
CREATE TABLE IF NOT EXISTS django_content_type (
    id BIGSERIAL PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE(app_label, model)
);

-- Criar tabela de permissões
CREATE TABLE IF NOT EXISTS auth_permission (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id BIGINT NOT NULL REFERENCES django_content_type(id),
    codename VARCHAR(100) NOT NULL,
    UNIQUE(content_type_id, codename)
);

CREATE INDEX IF NOT EXISTS idx_auth_permission_content_type_id ON auth_permission(content_type_id);

-- Criar tabela de grupos
CREATE TABLE IF NOT EXISTS auth_group (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE
);

-- Criar tabela de permissões de grupo
CREATE TABLE IF NOT EXISTS auth_group_permissions (
    id BIGSERIAL PRIMARY KEY,
    group_id BIGINT NOT NULL REFERENCES auth_group(id),
    permission_id BIGINT NOT NULL REFERENCES auth_permission(id),
    UNIQUE(group_id, permission_id)
);

CREATE INDEX IF NOT EXISTS idx_auth_group_permissions_group_id ON auth_group_permissions(group_id);
CREATE INDEX IF NOT EXISTS idx_auth_group_permissions_permission_id ON auth_group_permissions(permission_id);
