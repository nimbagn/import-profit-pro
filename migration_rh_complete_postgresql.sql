-- Migration complète RH : Tables pour gestion du personnel et activités
-- Date: 2025-01-XX
-- Base de données: PostgreSQL
-- Compatible avec PostgreSQL 12+

-- =========================================================
-- 1. TABLE user_activity_logs (si elle n'existe pas)
-- =========================================================
CREATE TABLE IF NOT EXISTS user_activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    action VARCHAR(100) NOT NULL,
    module VARCHAR(50) NULL,
    activity_metadata JSONB NULL,
    ip_address VARCHAR(45) NULL,
    user_agent VARCHAR(500) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE CASCADE
);

-- Index pour user_activity_logs
CREATE INDEX IF NOT EXISTS idx_activity_user ON user_activity_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_activity_action ON user_activity_logs (action);
CREATE INDEX IF NOT EXISTS idx_activity_module ON user_activity_logs (module);
CREATE INDEX IF NOT EXISTS idx_activity_created ON user_activity_logs (created_at);
CREATE INDEX IF NOT EXISTS idx_activity_user_action ON user_activity_logs (user_id, action);

COMMENT ON TABLE user_activity_logs IS 'Journal des activités et interactions des utilisateurs';

-- =========================================================
-- 2. TABLE employees (employés externes)
-- =========================================================
CREATE TYPE employment_status_enum AS ENUM ('active', 'inactive', 'suspended', 'terminated', 'on_leave');
CREATE TYPE gender_enum AS ENUM ('M', 'F');

CREATE TABLE IF NOT EXISTS employees (
    id BIGSERIAL PRIMARY KEY,
    employee_number VARCHAR(50) NOT NULL UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NULL UNIQUE,
    phone VARCHAR(20) NULL,
    phone_secondary VARCHAR(20) NULL,
    gender gender_enum NULL,
    date_of_birth DATE NULL,
    national_id VARCHAR(50) NULL,
    address VARCHAR(500) NULL,
    city VARCHAR(100) NULL,
    emergency_contact_name VARCHAR(200) NULL,
    emergency_contact_phone VARCHAR(20) NULL,
    emergency_contact_relation VARCHAR(50) NULL,
    department VARCHAR(100) NULL,
    position VARCHAR(100) NOT NULL,
    manager_id BIGINT NULL,
    region_id BIGINT NULL,
    depot_id BIGINT NULL,
    employment_status employment_status_enum NOT NULL DEFAULT 'active',
    hire_date DATE NOT NULL DEFAULT CURRENT_DATE,
    termination_date DATE NULL,
    user_id BIGINT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    created_by_id BIGINT NULL,
    CONSTRAINT fk_employee_manager FOREIGN KEY (manager_id) REFERENCES employees (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_employee_region FOREIGN KEY (region_id) REFERENCES regions (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_employee_depot FOREIGN KEY (depot_id) REFERENCES depots (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_employee_user FOREIGN KEY (user_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_employee_created_by FOREIGN KEY (created_by_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- Index pour employees
CREATE INDEX IF NOT EXISTS idx_employee_number ON employees (employee_number);
CREATE INDEX IF NOT EXISTS idx_employee_name ON employees (last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_employee_status ON employees (employment_status);
CREATE INDEX IF NOT EXISTS idx_employee_department ON employees (department);
CREATE INDEX IF NOT EXISTS idx_employee_position ON employees (position);
CREATE INDEX IF NOT EXISTS idx_employee_region ON employees (region_id);
CREATE INDEX IF NOT EXISTS idx_employee_depot ON employees (depot_id);
CREATE INDEX IF NOT EXISTS idx_employee_user ON employees (user_id);

COMMENT ON TABLE employees IS 'Personnel externe sans accès direct à la plateforme';

-- =========================================================
-- 3. TABLE employee_contracts (contrats)
-- =========================================================
CREATE TYPE contract_type_enum AS ENUM ('CDI', 'CDD', 'Stage', 'Freelance', 'Interim', 'Autre');
CREATE TYPE contract_status_enum AS ENUM ('draft', 'active', 'expired', 'terminated', 'cancelled');

CREATE TABLE IF NOT EXISTS employee_contracts (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    contract_number VARCHAR(100) NOT NULL UNIQUE,
    contract_type contract_type_enum NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    salary DECIMAL(12, 2) NULL,
    currency VARCHAR(3) DEFAULT 'MAD',
    status contract_status_enum NOT NULL DEFAULT 'draft',
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    created_by_id BIGINT NULL,
    CONSTRAINT fk_contract_employee FOREIGN KEY (employee_id) REFERENCES employees (id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_contract_created_by FOREIGN KEY (created_by_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- Index pour employee_contracts
CREATE INDEX IF NOT EXISTS idx_contract_employee ON employee_contracts (employee_id);
CREATE INDEX IF NOT EXISTS idx_contract_number ON employee_contracts (contract_number);
CREATE INDEX IF NOT EXISTS idx_contract_type ON employee_contracts (contract_type);
CREATE INDEX IF NOT EXISTS idx_contract_status ON employee_contracts (status);
CREATE INDEX IF NOT EXISTS idx_contract_dates ON employee_contracts (start_date, end_date);

COMMENT ON TABLE employee_contracts IS 'Contrats des employés';

-- =========================================================
-- 4. TABLE employee_trainings (formations)
-- =========================================================
CREATE TYPE training_type_enum AS ENUM ('Formation', 'Certification', 'Stage', 'Conference', 'Workshop', 'Autre');
CREATE TYPE training_status_enum AS ENUM ('planned', 'in_progress', 'completed', 'cancelled');

CREATE TABLE IF NOT EXISTS employee_trainings (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    training_name VARCHAR(200) NOT NULL,
    training_type training_type_enum NOT NULL,
    provider VARCHAR(200) NULL,
    start_date DATE NOT NULL,
    end_date DATE NULL,
    status training_status_enum NOT NULL DEFAULT 'planned',
    cost DECIMAL(10, 2) NULL,
    certificate_number VARCHAR(100) NULL,
    notes TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    created_by_id BIGINT NULL,
    CONSTRAINT fk_training_employee FOREIGN KEY (employee_id) REFERENCES employees (id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_training_created_by FOREIGN KEY (created_by_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL
);

-- Index pour employee_trainings
CREATE INDEX IF NOT EXISTS idx_training_employee ON employee_trainings (employee_id);
CREATE INDEX IF NOT EXISTS idx_training_type ON employee_trainings (training_type);
CREATE INDEX IF NOT EXISTS idx_training_status ON employee_trainings (status);
CREATE INDEX IF NOT EXISTS idx_training_dates ON employee_trainings (start_date, end_date);

COMMENT ON TABLE employee_trainings IS 'Formations des employés';

-- =========================================================
-- 5. TABLE employee_evaluations (évaluations)
-- =========================================================
CREATE TYPE evaluation_type_enum AS ENUM ('Performance', 'Annuelle', 'Probation', 'Promotion', 'Autre');
CREATE TYPE evaluation_status_enum AS ENUM ('draft', 'in_progress', 'completed', 'cancelled');

CREATE TABLE IF NOT EXISTS employee_evaluations (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    evaluation_type evaluation_type_enum NOT NULL,
    evaluation_date DATE NOT NULL,
    evaluator_id BIGINT NOT NULL,
    overall_rating DECIMAL(3, 2) NULL CHECK (overall_rating >= 0 AND overall_rating <= 5),
    strengths TEXT NULL,
    areas_for_improvement TEXT NULL,
    goals TEXT NULL,
    comments TEXT NULL,
    status evaluation_status_enum NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    CONSTRAINT fk_evaluation_employee FOREIGN KEY (employee_id) REFERENCES employees (id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_evaluation_evaluator FOREIGN KEY (evaluator_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Index pour employee_evaluations
CREATE INDEX IF NOT EXISTS idx_evaluation_employee ON employee_evaluations (employee_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_type ON employee_evaluations (evaluation_type);
CREATE INDEX IF NOT EXISTS idx_evaluation_status ON employee_evaluations (status);
CREATE INDEX IF NOT EXISTS idx_evaluation_date ON employee_evaluations (evaluation_date);
CREATE INDEX IF NOT EXISTS idx_evaluation_evaluator ON employee_evaluations (evaluator_id);

COMMENT ON TABLE employee_evaluations IS 'Évaluations des employés';

-- =========================================================
-- 6. TABLE employee_absences (absences)
-- =========================================================
CREATE TYPE absence_type_enum AS ENUM ('Congé', 'Maladie', 'Maternité', 'Paternité', 'Formation', 'Mission', 'Autre');
CREATE TYPE absence_status_enum AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

CREATE TABLE IF NOT EXISTS employee_absences (
    id BIGSERIAL PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    absence_type absence_type_enum NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_count DECIMAL(5, 2) NOT NULL,
    reason TEXT NULL,
    status absence_status_enum NOT NULL DEFAULT 'pending',
    approved_by_id BIGINT NULL,
    approved_at TIMESTAMP NULL,
    rejection_reason TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL,
    created_by_id BIGINT NULL,
    CONSTRAINT fk_absence_employee FOREIGN KEY (employee_id) REFERENCES employees (id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_absence_approved_by FOREIGN KEY (approved_by_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT fk_absence_created_by FOREIGN KEY (created_by_id) REFERENCES users (id) ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT chk_absence_dates CHECK (end_date >= start_date)
);

-- Index pour employee_absences
CREATE INDEX IF NOT EXISTS idx_absence_employee ON employee_absences (employee_id);
CREATE INDEX IF NOT EXISTS idx_absence_type ON employee_absences (absence_type);
CREATE INDEX IF NOT EXISTS idx_absence_status ON employee_absences (status);
CREATE INDEX IF NOT EXISTS idx_absence_dates ON employee_absences (start_date, end_date);

COMMENT ON TABLE employee_absences IS 'Absences des employés';

-- =========================================================
-- FIN DE LA MIGRATION
-- =========================================================

-- Vérification des tables créées
DO $$
BEGIN
    RAISE NOTICE '✅ Migration RH PostgreSQL terminée avec succès!';
    RAISE NOTICE '📊 Tables créées:';
    RAISE NOTICE '   - user_activity_logs';
    RAISE NOTICE '   - employees';
    RAISE NOTICE '   - employee_contracts';
    RAISE NOTICE '   - employee_trainings';
    RAISE NOTICE '   - employee_evaluations';
    RAISE NOTICE '   - employee_absences';
END $$;

