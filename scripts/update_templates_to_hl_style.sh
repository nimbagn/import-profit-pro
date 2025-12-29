#!/bin/bash
# Script pour mettre à jour tous les templates avec le style Hapag-Lloyd

echo "🔄 Mise à jour des templates avec le style Hapag-Lloyd..."

# Remplacements généraux
find templates -name "*.html" -type f -exec sed -i '' \
  -e 's/btn-premium/btn-hl btn-hl-primary/g' \
  -e 's/table-premium/table-hl/g' \
  -e 's/badge-premium/badge-hl/g' \
  -e 's/card-premium/card-hl/g' \
  -e 's/form-card/form-hl/g' \
  -e 's/form-control/form-hl-input/g' \
  -e 's/form-label/form-hl-label/g' \
  {} \;

echo "✅ Remplacements effectués"
echo ""
echo "📝 Note: Vérifiez manuellement les templates pour les ajustements spécifiques"

