#!/bin/bash
# Script simple pour vérifier l'utilisateur admin

echo "============================================================"
echo "VÉRIFICATION DE L'UTILISATEUR ADMIN"
echo "============================================================"
echo ""
echo "Exécutez cette commande dans MySQL:"
echo ""
echo "mysql -u root -p madargn < VERIFIER_ADMIN.sql"
echo ""
echo "OU connectez-vous à MySQL et exécutez:"
echo ""
echo "USE madargn;"
echo "SELECT * FROM users WHERE username = 'admin';"
echo "SELECT * FROM roles WHERE code = 'admin';"
echo ""
echo "============================================================"

