-- Script SQL direct pour créer les tables du chat
-- À exécuter avec: mysql -u root -p madargn < scripts/create_chat_tables_direct.sql

USE madargn;

-- Table des conversations
CREATE TABLE IF NOT EXISTS `chat_rooms` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(200) NULL,
    `room_type` ENUM('direct', 'group', 'channel') NOT NULL DEFAULT 'direct',
    `created_by_id` BIGINT UNSIGNED NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NULL ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatroom_creator` (`created_by_id`),
    INDEX `idx_chatroom_type` (`room_type`),
    CONSTRAINT `fk_chatrooms_creator` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des participants
CREATE TABLE IF NOT EXISTS `chat_room_members` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `room_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `role` ENUM('member', 'admin', 'moderator') NOT NULL DEFAULT 'member',
    `joined_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `last_read_at` DATETIME NULL,
    `is_muted` BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_room_member` (`room_id`, `user_id`),
    INDEX `idx_chatmember_room` (`room_id`),
    INDEX `idx_chatmember_user` (`user_id`),
    INDEX `idx_chatmember_lastread` (`last_read_at`),
    CONSTRAINT `fk_chatmembers_room` FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatmembers_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des messages
CREATE TABLE IF NOT EXISTS `chat_messages` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `room_id` BIGINT UNSIGNED NOT NULL,
    `sender_id` BIGINT UNSIGNED NOT NULL,
    `content` TEXT NOT NULL,
    `message_type` ENUM('text', 'file', 'system') NOT NULL DEFAULT 'text',
    `is_edited` BOOLEAN NOT NULL DEFAULT FALSE,
    `edited_at` DATETIME NULL,
    `is_deleted` BOOLEAN NOT NULL DEFAULT FALSE,
    `deleted_at` DATETIME NULL,
    `reply_to_id` BIGINT UNSIGNED NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatmsg_room` (`room_id`),
    INDEX `idx_chatmsg_sender` (`sender_id`),
    INDEX `idx_chatmsg_created` (`created_at`),
    INDEX `idx_chatmsg_reply` (`reply_to_id`),
    INDEX `idx_chatmsg_room_created` (`room_id`, `created_at`),
    CONSTRAINT `fk_chatmessages_room` FOREIGN KEY (`room_id`) REFERENCES `chat_rooms` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatmessages_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_chatmessages_reply` FOREIGN KEY (`reply_to_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des pièces jointes
CREATE TABLE IF NOT EXISTS `chat_attachments` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` BIGINT UNSIGNED NOT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_path` VARCHAR(500) NOT NULL,
    `file_size` BIGINT UNSIGNED NOT NULL,
    `file_type` VARCHAR(100) NOT NULL,
    `file_extension` VARCHAR(10) NOT NULL,
    `thumbnail_path` VARCHAR(500) NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_chatattach_message` (`message_id`),
    INDEX `idx_chatattach_type` (`file_type`),
    CONSTRAINT `fk_chatattachments_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des marqueurs de lecture
CREATE TABLE IF NOT EXISTS `chat_message_reads` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `message_id` BIGINT UNSIGNED NOT NULL,
    `user_id` BIGINT UNSIGNED NOT NULL,
    `read_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_msg_read` (`message_id`, `user_id`),
    INDEX `idx_chatread_message` (`message_id`),
    INDEX `idx_chatread_user` (`user_id`),
    CONSTRAINT `fk_chatreads_message` FOREIGN KEY (`message_id`) REFERENCES `chat_messages` (`id`) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_chatreads_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SELECT 'Tables du chat créées avec succès!' AS message;

