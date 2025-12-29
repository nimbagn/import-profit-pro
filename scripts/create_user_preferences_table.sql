-- Script SQL pour créer la table user_preferences
-- Système de thèmes personnalisables

CREATE TABLE IF NOT EXISTS user_preferences (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id BIGINT UNSIGNED NOT NULL,
    theme_name VARCHAR(50) NOT NULL DEFAULT 'hapag-lloyd',
    color_mode VARCHAR(20) NOT NULL DEFAULT 'light',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY unique_user_preference (user_id),
    CONSTRAINT fk_user_pref_user FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON UPDATE CASCADE 
        ON DELETE CASCADE,
    INDEX idx_user_pref_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insérer des préférences par défaut pour les utilisateurs existants
INSERT INTO user_preferences (user_id, theme_name, color_mode)
SELECT id, 'hapag-lloyd', 'light'
FROM users
WHERE id NOT IN (SELECT user_id FROM user_preferences);

