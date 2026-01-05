-- =========================================================
-- Script pour ajouter les permissions messaging au rôle superviseur
-- =========================================================
-- Date : 4 Janvier 2026
-- Description : Ajoute les permissions de gestion de la messagerie
--               au rôle superviseur (read, send_sms, send_whatsapp, send_otp, manage_contacts)
-- Compatible PostgreSQL
-- =========================================================

DO $$
DECLARE
    supervisor_permissions JSONB;
    messaging_perms JSONB := '["read", "update", "send_sms", "send_whatsapp", "send_otp", "manage_contacts"]'::JSONB;
BEGIN
    -- Récupérer les permissions actuelles du superviseur
    SELECT permissions INTO supervisor_permissions
    FROM roles
    WHERE code = 'supervisor';
    
    -- Si le rôle existe
    IF supervisor_permissions IS NOT NULL THEN
        -- Ajouter les permissions messaging
        supervisor_permissions := supervisor_permissions || jsonb_build_object('messaging', messaging_perms);
        
        -- Mettre à jour le rôle
        UPDATE roles
        SET permissions = supervisor_permissions
        WHERE code = 'supervisor';
        
        RAISE NOTICE '✅ Permissions messaging ajoutées au rôle superviseur';
    ELSE
        RAISE WARNING '❌ Rôle superviseur non trouvé';
    END IF;
END $$;

-- Vérification
SELECT 
    code, 
    name,
    permissions->'messaging' as messaging_permissions 
FROM roles 
WHERE code = 'supervisor';

