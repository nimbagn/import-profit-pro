-- =========================================================
-- MIGRATION : TABLES CHAT INTERNE (PostgreSQL)
-- Date : 3 Janvier 2026
-- Description : Script idempotent pour créer les tables
--                du module chat en PostgreSQL
-- =========================================================
-- IMPORTANT : Ce script est idempotent et peut être exécuté
--             plusieurs fois sans erreur
-- =========================================================

BEGIN;

-- =========================================================
-- 1. CRÉER LES TYPES ENUM SI NÉCESSAIRES
-- =========================================================
DO $$
BEGIN
    -- Type room_type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'room_type') THEN
        CREATE TYPE room_type AS ENUM ('direct', 'group', 'channel');
        RAISE NOTICE '✅ Type room_type créé';
    ELSE
        RAISE NOTICE 'ℹ️  Type room_type existe déjà';
    END IF;
    
    -- Type member_role
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'member_role') THEN
        CREATE TYPE member_role AS ENUM ('member', 'admin', 'moderator');
        RAISE NOTICE '✅ Type member_role créé';
    ELSE
        RAISE NOTICE 'ℹ️  Type member_role existe déjà';
    END IF;
    
    -- Type message_type
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'message_type') THEN
        CREATE TYPE message_type AS ENUM ('text', 'file', 'system');
        RAISE NOTICE '✅ Type message_type créé';
    ELSE
        RAISE NOTICE 'ℹ️  Type message_type existe déjà';
    END IF;
END $$;

-- =========================================================
-- 2. TABLE chat_rooms
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chat_rooms'
    ) THEN
        CREATE TABLE chat_rooms (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(200) NULL,
            room_type room_type NOT NULL DEFAULT 'direct',
            created_by_id BIGINT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NULL,
            CONSTRAINT fk_chatrooms_creator 
                FOREIGN KEY (created_by_id) 
                REFERENCES users(id) 
                ON UPDATE CASCADE 
                ON DELETE RESTRICT
        );
        
        CREATE INDEX idx_chatroom_creator ON chat_rooms(created_by_id);
        CREATE INDEX idx_chatroom_type ON chat_rooms(room_type);
        
        RAISE NOTICE '✅ Table chat_rooms créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table chat_rooms existe déjà';
    END IF;
END $$;

-- =========================================================
-- 3. TABLE chat_room_members
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chat_room_members'
    ) THEN
        CREATE TABLE chat_room_members (
            id BIGSERIAL PRIMARY KEY,
            room_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            role member_role NOT NULL DEFAULT 'member',
            joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_read_at TIMESTAMP NULL,
            is_muted BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT uq_room_member UNIQUE (room_id, user_id),
            CONSTRAINT fk_chatmembers_room 
                FOREIGN KEY (room_id) 
                REFERENCES chat_rooms(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE,
            CONSTRAINT fk_chatmembers_user 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE
        );
        
        CREATE INDEX idx_chatmember_room ON chat_room_members(room_id);
        CREATE INDEX idx_chatmember_user ON chat_room_members(user_id);
        CREATE INDEX idx_chatmember_lastread ON chat_room_members(last_read_at);
        
        RAISE NOTICE '✅ Table chat_room_members créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table chat_room_members existe déjà';
    END IF;
END $$;

-- =========================================================
-- 4. TABLE chat_messages
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chat_messages'
    ) THEN
        CREATE TABLE chat_messages (
            id BIGSERIAL PRIMARY KEY,
            room_id BIGINT NOT NULL,
            sender_id BIGINT NOT NULL,
            content TEXT NOT NULL,
            message_type message_type NOT NULL DEFAULT 'text',
            is_edited BOOLEAN NOT NULL DEFAULT FALSE,
            edited_at TIMESTAMP NULL,
            is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
            deleted_at TIMESTAMP NULL,
            reply_to_id BIGINT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_chatmessages_room 
                FOREIGN KEY (room_id) 
                REFERENCES chat_rooms(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE,
            CONSTRAINT fk_chatmessages_sender 
                FOREIGN KEY (sender_id) 
                REFERENCES users(id) 
                ON UPDATE CASCADE 
                ON DELETE RESTRICT,
            CONSTRAINT fk_chatmessages_reply 
                FOREIGN KEY (reply_to_id) 
                REFERENCES chat_messages(id) 
                ON UPDATE CASCADE 
                ON DELETE SET NULL
        );
        
        CREATE INDEX idx_chatmsg_room ON chat_messages(room_id);
        CREATE INDEX idx_chatmsg_sender ON chat_messages(sender_id);
        CREATE INDEX idx_chatmsg_created ON chat_messages(created_at);
        CREATE INDEX idx_chatmsg_reply ON chat_messages(reply_to_id);
        CREATE INDEX idx_chatmsg_room_created ON chat_messages(room_id, created_at);
        
        RAISE NOTICE '✅ Table chat_messages créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table chat_messages existe déjà';
    END IF;
END $$;

-- =========================================================
-- 5. TABLE chat_attachments
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chat_attachments'
    ) THEN
        CREATE TABLE chat_attachments (
            id BIGSERIAL PRIMARY KEY,
            message_id BIGINT NOT NULL,
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size BIGINT NOT NULL,
            file_type VARCHAR(100) NOT NULL,
            file_extension VARCHAR(10) NOT NULL,
            thumbnail_path VARCHAR(500) NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_chatattachments_message 
                FOREIGN KEY (message_id) 
                REFERENCES chat_messages(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE
        );
        
        CREATE INDEX idx_chatattach_message ON chat_attachments(message_id);
        CREATE INDEX idx_chatattach_type ON chat_attachments(file_type);
        
        RAISE NOTICE '✅ Table chat_attachments créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table chat_attachments existe déjà';
    END IF;
END $$;

-- =========================================================
-- 6. TABLE chat_message_reads
-- =========================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chat_message_reads'
    ) THEN
        CREATE TABLE chat_message_reads (
            id BIGSERIAL PRIMARY KEY,
            message_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            read_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_msg_read UNIQUE (message_id, user_id),
            CONSTRAINT fk_chatreads_message 
                FOREIGN KEY (message_id) 
                REFERENCES chat_messages(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE,
            CONSTRAINT fk_chatreads_user 
                FOREIGN KEY (user_id) 
                REFERENCES users(id) 
                ON UPDATE CASCADE 
                ON DELETE CASCADE
        );
        
        CREATE INDEX idx_chatread_message ON chat_message_reads(message_id);
        CREATE INDEX idx_chatread_user ON chat_message_reads(user_id);
        
        RAISE NOTICE '✅ Table chat_message_reads créée';
    ELSE
        RAISE NOTICE 'ℹ️  Table chat_message_reads existe déjà';
    END IF;
END $$;

COMMIT;

-- =========================================================
-- RÉSUMÉ
-- =========================================================
DO $$
BEGIN
    RAISE NOTICE '=========================================================';
    RAISE NOTICE '✅ Migration des tables chat terminée avec succès';
    RAISE NOTICE '=========================================================';
    RAISE NOTICE 'Tables créées/vérifiées :';
    RAISE NOTICE '  - chat_rooms';
    RAISE NOTICE '  - chat_room_members';
    RAISE NOTICE '  - chat_messages';
    RAISE NOTICE '  - chat_attachments';
    RAISE NOTICE '  - chat_message_reads';
    RAISE NOTICE '=========================================================';
END $$;

