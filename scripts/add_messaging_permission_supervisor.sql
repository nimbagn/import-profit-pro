-- =========================================================
-- Script pour ajouter les permissions messaging au rôle superviseur
-- =========================================================
-- Date : 4 Janvier 2026
-- Description : Ajoute les permissions de gestion de la messagerie
--               au rôle superviseur (read, send_sms, send_whatsapp, send_otp, manage_contacts)
-- Compatible MySQL
-- =========================================================

-- Pour MySQL
UPDATE roles 
SET permissions = JSON_SET(
    permissions, 
    '$.messaging', 
    JSON_ARRAY('read', 'send_sms', 'send_whatsapp', 'send_otp', 'manage_contacts')
) 
WHERE code = 'supervisor';

-- Vérification
SELECT 
    code, 
    name,
    JSON_EXTRACT(permissions, '$.messaging') as messaging_permissions 
FROM roles 
WHERE code = 'supervisor';

