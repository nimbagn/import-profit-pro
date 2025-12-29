# pdf_generator.py
# Générateur de rapports PDF pour Import Profit Pro

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from datetime import datetime, UTC
from decimal import Decimal
from io import BytesIO


class PDFGenerator:
    """Générateur de rapports PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        # Style titre principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#003d82'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Style sous-titre
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#0052a5'),
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        
        # Style normal avec espacement
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            leading=14
        ))
        
        # Style pour les labels
        self.styles.add(ParagraphStyle(
            name='Label',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7a8a9a'),
            fontName='Helvetica-Oblique'
        ))
        
        # Style pour les valeurs
        self.styles.add(ParagraphStyle(
            name='Value',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        ))
    
    def format_currency(self, amount, currency='GNF', exchange_rate=None):
        """Formate un montant en devise avec conversion optionnelle"""
        if amount is None:
            return '0'
        if isinstance(amount, Decimal):
            amount = float(amount)
        
        # Convertir si nécessaire (amount est en GNF)
        if currency != 'GNF' and exchange_rate and exchange_rate > 0:
            amount = amount / exchange_rate
            # Pour USD et EUR, utiliser 2 décimales, pour XOF utiliser 0
            if currency in ['USD', 'EUR']:
                formatted = f"{amount:,.2f}".replace(',', ' ')
            else:
                formatted = f"{amount:,.0f}".replace(',', ' ')
        else:
            # Format avec espace comme séparateur de milliers
            formatted = f"{amount:,.0f}".replace(',', ' ')
        
        return f"{formatted} {currency}"
    
    def format_date(self, date_obj):
        """Formate une date"""
        if date_obj is None:
            return 'N/A'
        if isinstance(date_obj, str):
            return date_obj
        return date_obj.strftime('%d/%m/%Y %H:%M')
    
    def create_header_footer(self, canvas_obj, doc, title, page_size=None):
        """Crée l'en-tête et le pied de page"""
        if page_size is None:
            page_size = A4
        
        # En-tête
        canvas_obj.saveState()
        canvas_obj.setFillColor(colors.HexColor('#003d82'))
        canvas_obj.rect(0, page_size[1] - 2*cm, page_size[0], 2*cm, fill=1)
        canvas_obj.setFillColorRGB(1, 1, 1)  # Blanc
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawString(2*cm, page_size[1] - 1.2*cm, 'IMPORT PROFIT PRO')
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.drawString(2*cm, page_size[1] - 1.6*cm, title)
        
        # Pied de page
        canvas_obj.setFillColor(colors.HexColor('#7a8a9a'))
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(2*cm, 1*cm, f'Généré le {datetime.now(UTC).strftime("%d/%m/%Y %H:%M")}')
        canvas_obj.drawRightString(page_size[0] - 2*cm, 1*cm, f'Page {doc.page}')
        canvas_obj.restoreState()
    
    def calculate_table_width(self, col_widths):
        """Calcule la largeur totale d'un tableau"""
        return sum(col_widths)
    
    def adjust_table_for_page(self, col_widths, page_width, min_col_width=1.5*cm):
        """Ajuste les largeurs de colonnes pour qu'elles tiennent sur la page"""
        total_width = sum(col_widths)
        available_width = page_width - 4*cm  # Marges gauche et droite
        
        if total_width <= available_width:
            # Le tableau tient, on peut garder les largeurs originales
            return col_widths
        
        # Le tableau est trop large, on ajuste proportionnellement
        ratio = available_width / total_width
        adjusted_widths = [max(w * ratio, min_col_width) for w in col_widths]
        
        # Ajuster si la somme dépasse encore
        total_adjusted = sum(adjusted_widths)
        if total_adjusted > available_width:
            ratio2 = available_width / total_adjusted
            adjusted_widths = [w * ratio2 for w in adjusted_widths]
        
        return adjusted_widths
    
    def determine_orientation(self, col_widths, num_cols):
        """Détermine l'orientation optimale (portrait ou paysage)"""
        # Largeur disponible en portrait
        portrait_width = A4[0] - 4*cm
        # Largeur disponible en paysage
        landscape_width = A4[1] - 4*cm
        
        total_width = sum(col_widths)
        
        # Si le tableau a beaucoup de colonnes ou est très large, utiliser paysage
        if num_cols >= 6 or total_width > portrait_width:
            return landscape(A4), landscape_width
        else:
            return A4, portrait_width
    
    def generate_simulation_pdf(self, simulation, simulation_items, currency='GNF'):
        """Génère un PDF pour une simulation avec orientation automatique et conversion de devise"""
        from decimal import Decimal
        
        # Déterminer le taux de change pour la conversion
        exchange_rate = None
        if currency == 'USD':
            exchange_rate = float(simulation.rate_usd) if simulation.rate_usd else None
        elif currency == 'EUR':
            exchange_rate = float(simulation.rate_eur) if simulation.rate_eur else None
        elif currency == 'XOF':
            exchange_rate = float(simulation.rate_xof) if simulation.rate_xof else None
        
        # Calculer les données détaillées (comme dans preview)
        total_purchase_value = Decimal('0')
        total_weight = Decimal('0')
        total_selling_value = Decimal('0')
        items_with_cost = []
        
        for item in simulation_items:
            rate = simulation.rate_usd
            if hasattr(item, 'purchase_currency'):
                if item.purchase_currency == 'EUR':
                    rate = simulation.rate_eur
                elif item.purchase_currency == 'XOF':
                    rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
            
            purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
            item_value = purchase_price_gnf * Decimal(str(item.quantity))
            item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg or 0))
            
            total_purchase_value += item_value
            total_weight += item_weight
            total_selling_value += Decimal(str(item.selling_price_gnf)) * Decimal(str(item.quantity))
        
        # Calculer les coûts logistiques
        total_fixed_costs = (
            Decimal(str(simulation.customs_gnf or 0)) +
            Decimal(str(simulation.handling_gnf or 0)) +
            Decimal(str(simulation.others_gnf or 0)) +
            Decimal(str(simulation.transport_fixed_gnf or 0))
        )
        total_variable_costs = total_weight * Decimal(str(simulation.transport_per_kg_gnf or 0))
        total_logistics_costs = total_fixed_costs + total_variable_costs
        
        # Calculer le prix de revient pour chaque article
        for item in simulation_items:
            rate = simulation.rate_usd
            if hasattr(item, 'purchase_currency'):
                if item.purchase_currency == 'EUR':
                    rate = simulation.rate_eur
                elif item.purchase_currency == 'XOF':
                    rate = simulation.rate_xof if simulation.rate_xof else simulation.rate_usd
            
            purchase_price_gnf = Decimal(str(item.purchase_price)) * Decimal(str(rate))
            item_value = purchase_price_gnf * Decimal(str(item.quantity))
            item_weight = Decimal(str(item.quantity)) * Decimal(str(item.unit_weight_kg or 0))
            
            logistics_cost = Decimal('0')
            if simulation.basis == 'value' and total_purchase_value > 0:
                logistics_cost = (item_value / total_purchase_value) * total_logistics_costs
            elif simulation.basis == 'weight' and total_weight > 0:
                logistics_cost = (item_weight / total_weight) * total_logistics_costs
            
            logistics_per_unit = logistics_cost / Decimal(str(item.quantity)) if item.quantity > 0 else Decimal('0')
            cost_price_per_unit = purchase_price_gnf + logistics_per_unit
            
            selling_price = Decimal(str(item.selling_price_gnf))
            margin = selling_price - cost_price_per_unit
            margin_pct = (margin / cost_price_per_unit * 100) if cost_price_per_unit > 0 else Decimal('0')
            
            items_with_cost.append({
                'item': item,
                'purchase_price_gnf': purchase_price_gnf,
                'logistics_per_unit': logistics_per_unit,
                'cost_price_per_unit': cost_price_per_unit,
                'total_cost': cost_price_per_unit * Decimal(str(item.quantity)),
                'selling_price': selling_price,
                'margin': margin,
                'margin_pct': margin_pct
            })
        
        total_cost_price = sum(item['total_cost'] for item in items_with_cost)
        total_margin = sum(item['margin'] * item['item'].quantity for item in items_with_cost)
        total_margin_pct = (total_margin / total_cost_price * 100) if total_cost_price > 0 else Decimal('0')
        
        # Déterminer l'orientation et les largeurs de colonnes
        # Tableau avec 8 colonnes : Article, Qté, Prix Achat, Coûts Log., Prix Revient, Prix Vente, Marge, Marge %
        original_col_widths = [4*cm, 1.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2*cm]
        page_size, available_width = self.determine_orientation(original_col_widths, 8)
        adjusted_col_widths = self.adjust_table_for_page(original_col_widths, available_width, min_col_width=1.2*cm)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=page_size,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=3*cm, bottomMargin=2*cm)
        
        story = []
        
        # Titre avec devise
        title_text = f'SIMULATION DE RENTABILITÉ ({currency})'
        story.append(Paragraph(title_text, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # Informations de la simulation (tableau compact)
        info_data = [
            ['ID', str(simulation.id), 'Taux USD', f"{simulation.rate_usd or 0:,.0f}".replace(',', ' ') + ' GNF'],
            ['Date', self.format_date(simulation.created_at), 'Taux EUR', f"{simulation.rate_eur or 0:,.0f}".replace(',', ' ') + ' GNF'],
        ]
        
        if hasattr(simulation, 'customs_gnf'):
            info_data.extend([
                ['Douane', self.format_currency(simulation.customs_gnf), 'Manutention', self.format_currency(simulation.handling_gnf)],
                ['Transport Fixe', self.format_currency(simulation.transport_fixed_gnf), 'Transport/kg', self.format_currency(simulation.transport_per_kg_gnf)],
            ])
        
        info_table = Table(info_data, colWidths=[2.5*cm, 4*cm, 2.5*cm, 4*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau des articles avec toutes les colonnes
        story.append(Paragraph('ARTICLES DE LA SIMULATION', self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2*cm))
        
        headers = ['Article', 'Qté', 'Prix Achat', 'Coûts Log.', 'Prix Revient', 'Prix Vente', 'Marge', 'Marge %']
        items_data = [headers]
        
        for item_data in items_with_cost:
            item = item_data['item']
            article_name = getattr(item, 'article_name', 'N/A')
            if hasattr(item, 'article') and item.article:
                article_name = item.article.name or article_name
            
            # Limiter la longueur du nom d'article
            max_name_len = int(adjusted_col_widths[0] / 0.3)  # Approximation
            article_name = article_name[:max_name_len] if len(article_name) > max_name_len else article_name
            
            items_data.append([
                article_name,
                f"{item.quantity:.2f}",
                self.format_currency(item_data['purchase_price_gnf'], currency, exchange_rate).replace(f' {currency}', ''),
                self.format_currency(item_data['logistics_per_unit'], currency, exchange_rate).replace(f' {currency}', ''),
                self.format_currency(item_data['cost_price_per_unit'], currency, exchange_rate).replace(f' {currency}', ''),
                self.format_currency(item_data['selling_price'], currency, exchange_rate).replace(f' {currency}', ''),
                self.format_currency(item_data['margin'], currency, exchange_rate).replace(f' {currency}', ''),
                f"{float(item_data['margin_pct']):.2f}%"
            ])
        
        # Ligne de total (sans balises HTML, le style sera appliqué via TableStyle)
        items_data.append([
            'TOTAL',
            '',
            self.format_currency(total_purchase_value, currency, exchange_rate).replace(f' {currency}', ''),
            self.format_currency(total_logistics_costs, currency, exchange_rate).replace(f' {currency}', ''),
            self.format_currency(total_cost_price, currency, exchange_rate).replace(f' {currency}', ''),
            self.format_currency(total_selling_value, currency, exchange_rate).replace(f' {currency}', ''),
            self.format_currency(total_margin, currency, exchange_rate).replace(f' {currency}', ''),
            f"{float(total_margin_pct):.2f}%"
        ])
        
        items_table = Table(items_data, colWidths=adjusted_col_widths)
        items_table.setStyle(TableStyle([
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d82')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Données
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#2c3e50')),
            ('ALIGN', (1, 1), (1, -2), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -2), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 7),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
            ('TOPPADDING', (0, 1), (-1, -2), 6),
            # Ligne de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#003d82')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('ALIGN', (0, -1), (0, -1), 'LEFT'),
            ('ALIGN', (2, -1), (-1, -1), 'RIGHT'),
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#003d82')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#003d82')),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Résumé financier compact (sans balises HTML)
        summary_data = [
            ['Total Achat', self.format_currency(total_purchase_value, currency, exchange_rate), 
             'Total Coûts Log.', self.format_currency(total_logistics_costs, currency, exchange_rate)],
            ['Total Prix Revient', self.format_currency(total_cost_price, currency, exchange_rate), 
             'Total Vente', self.format_currency(total_selling_value, currency, exchange_rate)],
            ['Marge Totale', self.format_currency(total_margin, currency, exchange_rate), 
             'Taux de Marge', f"{float(total_margin_pct):.2f}%"],
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#003d82')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#003d82')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
        ]))
        
        story.append(summary_table)
        
        # Générer le PDF avec la bonne orientation
        def header_footer(c, d):
            self.create_header_footer(c, d, 'Simulation de Rentabilité', page_size)
        
        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        
        buffer.seek(0)
        return buffer
    
    def generate_forecast_pdf(self, forecast, forecast_items, currency='GNF'):
        """Génère un PDF pour une prévision avec orientation automatique et conversion de devise"""
        # Déterminer le taux de change pour la conversion
        exchange_rate = None
        if hasattr(forecast, 'rate_usd') and forecast.rate_usd:
            if currency == 'USD':
                exchange_rate = float(forecast.rate_usd)
            elif currency == 'EUR' and hasattr(forecast, 'rate_eur') and forecast.rate_eur:
                exchange_rate = float(forecast.rate_eur)
            elif currency == 'XOF' and hasattr(forecast, 'rate_xof') and forecast.rate_xof:
                exchange_rate = float(forecast.rate_xof)
        
        # Déterminer l'orientation et les largeurs de colonnes
        # Tableau avec 5 colonnes : Article, Prévision, Réalisation, Écart, Taux
        original_col_widths = [5*cm, 3*cm, 3*cm, 3*cm, 2.5*cm]
        page_size, available_width = self.determine_orientation(original_col_widths, 5)
        adjusted_col_widths = self.adjust_table_for_page(original_col_widths, available_width, min_col_width=1.5*cm)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=page_size,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=3*cm, bottomMargin=2*cm)
        
        story = []
        
        # Titre avec devise
        title_text = f'PRÉVISION DE VENTES ({currency})'
        story.append(Paragraph(title_text, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # Informations de la prévision (compact)
        period = getattr(forecast, 'period', 'N/A')
        if hasattr(forecast, 'start_date') and hasattr(forecast, 'end_date'):
            if forecast.start_date and forecast.end_date:
                period = f"{forecast.start_date.strftime('%d/%m/%Y')} - {forecast.end_date.strftime('%d/%m/%Y')}"
        
        commercial = getattr(forecast, 'commercial_name', 'N/A')
        if hasattr(forecast, 'commercial') and forecast.commercial:
            commercial = forecast.commercial.username if hasattr(forecast.commercial, 'username') else commercial
        
        info_data = [
            ['ID', str(forecast.id), 'Période', period],
            ['Commercial', commercial, 'Date', self.format_date(forecast.created_at)],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau des articles
        story.append(Paragraph('DÉTAIL DES PRÉVISIONS', self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2*cm))
        
        headers = ['Article', 'Prévision', 'Réalisation', 'Écart', 'Taux %']
        items_data = [headers]
        
        total_forecast = Decimal('0')
        total_realization = Decimal('0')
        
        for item in forecast_items:
            article_name = getattr(item, 'article_name', 'N/A')
            if hasattr(item, 'article') and item.article:
                article_name = item.article.name or article_name
            elif hasattr(item, 'stock_item') and item.stock_item:
                article_name = item.stock_item.name or article_name
            
            forecast_qty = getattr(item, 'forecast_quantity', 0) or 0
            realization_qty = getattr(item, 'realized_quantity', 0) or 0
            variance = realization_qty - forecast_qty
            rate = (realization_qty / forecast_qty * 100) if forecast_qty > 0 else 0
            
            total_forecast += Decimal(str(forecast_qty))
            total_realization += Decimal(str(realization_qty))
            
            # Limiter la longueur du nom
            max_name_len = int(adjusted_col_widths[0] / 0.3)
            article_name = article_name[:max_name_len] if len(article_name) > max_name_len else article_name
            
            items_data.append([
                article_name,
                f"{forecast_qty:.2f}",
                f"{realization_qty:.2f}",
                f"{variance:.2f}",
                f"{rate:.1f}%"
            ])
        
        # Ligne de total (sans balises HTML)
        total_variance = total_realization - total_forecast
        total_rate = (float(total_realization) / float(total_forecast) * 100) if total_forecast > 0 else 0
        
        items_data.append([
            'TOTAL',
            f"{total_forecast:.2f}",
            f"{total_realization:.2f}",
            f"{total_variance:.2f}",
            f"{total_rate:.1f}%"
        ])
        
        items_table = Table(items_data, colWidths=adjusted_col_widths)
        items_table.setStyle(TableStyle([
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d82')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Données
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#2c3e50')),
            ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
            ('TOPPADDING', (0, 1), (-1, -2), 6),
            # Ligne de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#003d82')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('ALIGN', (1, -1), (-1, -1), 'CENTER'),
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#003d82')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#003d82')),
        ]))
        
        story.append(items_table)
        
        # Générer le PDF
        def header_footer(c, d):
            self.create_header_footer(c, d, 'Prévision de Ventes', page_size)
        
        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        
        buffer.seek(0)
        return buffer
    
    def generate_sales_pdf(self, sales_data, filters_info=None, currency='GNF'):
        """Génère un PDF pour les ventes de promotion"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=3*cm, bottomMargin=2*cm)
        
        story = []
        
        # Titre
        title_text = 'RAPPORT DES VENTES - PROMOTION'
        story.append(Paragraph(title_text, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # Informations des filtres
        if filters_info:
            info_data = []
            if filters_info.get('date_from'):
                info_data.append(['Date début:', filters_info['date_from']])
            if filters_info.get('date_to'):
                info_data.append(['Date fin:', filters_info['date_to']])
            if filters_info.get('member'):
                info_data.append(['Membre:', filters_info['member']])
            if filters_info.get('team'):
                info_data.append(['Équipe:', filters_info['team']])
            if filters_info.get('transaction_type'):
                info_data.append(['Type:', filters_info['transaction_type'].title()])
            
            if info_data:
                info_table = Table(info_data, colWidths=[4*cm, 12*cm])
                info_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(info_table)
                story.append(Spacer(1, 0.5*cm))
        
        # Tableau des ventes
        if sales_data:
            # En-têtes
            headers = ['Date', 'Réf.', 'Type', 'Membre', 'Équipe', 'Gamme', 'Qté', 'Montant', 'Commission']
            col_widths = [2*cm, 2*cm, 2*cm, 3*cm, 2.5*cm, 3*cm, 1.5*cm, 2.5*cm, 2.5*cm]
            
            # Données
            table_data = [headers]
            total_amount = Decimal('0')
            total_commission = Decimal('0')
            total_quantity = 0
            
            for sale in sales_data:
                date_str = sale.get('date', 'N/A')
                ref = sale.get('reference', 'N/A')[:10] if sale.get('reference') else 'N/A'
                trans_type = sale.get('type', 'N/A').title()
                member = sale.get('member', 'N/A')[:20] if sale.get('member') else 'N/A'
                team = sale.get('team', 'N/A')[:15] if sale.get('team') else 'N/A'
                gamme = sale.get('gamme', 'N/A')[:20] if sale.get('gamme') else 'N/A'
                qty = sale.get('quantity', 0)
                amount = Decimal(str(sale.get('amount', 0)))
                commission = Decimal(str(sale.get('commission', 0)))
                
                table_data.append([
                    date_str, ref, trans_type, member, team, gamme,
                    str(qty), self.format_currency(amount, currency),
                    self.format_currency(commission, currency)
                ])
                
                total_amount += amount
                total_commission += commission
                total_quantity += qty
            
            # Ligne de total
            table_data.append([
                'TOTAL', '', '', '', '', '',
                str(total_quantity),
                self.format_currency(total_amount, currency),
                self.format_currency(total_commission, currency)
            ])
            
            # Créer le tableau
            sales_table = Table(table_data, colWidths=col_widths, repeatRows=1)
            sales_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d82')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (3, 0), (5, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-2, -2), 8),
                ('FONTSIZE', (0, -1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
                ('TOPPADDING', (0, -1), (-1, -1), 10),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f7fa')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
            ]))
            
            story.append(sales_table)
            story.append(Spacer(1, 0.5*cm))
            
            # Résumé financier
            summary_data = [
                ['Total Quantité:', str(total_quantity)],
                ['Total Montant:', self.format_currency(total_amount, currency)],
                ['Total Commission:', self.format_currency(total_commission, currency)],
                ['Résultat Net:', self.format_currency(total_amount - total_commission, currency)]
            ]
            
            summary_table = Table(summary_data, colWidths=[5*cm, 11*cm])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
            ]))
            
            story.append(summary_table)
        else:
            story.append(Paragraph('Aucune vente trouvée pour les critères sélectionnés.', self.styles['CustomNormal']))
        
        # Générer le PDF
        def header_footer(c, d):
            self.create_header_footer(c, d, 'Rapport des Ventes - Promotion', A4)
        
        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        
        buffer.seek(0)
        return buffer
    
    def generate_stock_summary_pdf(self, stock_data, currency='GNF', exchange_rate=None):
        """Génère un PDF pour le récapitulatif de stock avec orientation automatique et conversion de devise"""
        # Déterminer l'orientation et les largeurs de colonnes
        # Tableau avec 4 colonnes : Article, Dépôt, Quantité, Valeur
        original_col_widths = [5*cm, 4*cm, 3*cm, 4*cm]
        page_size, available_width = self.determine_orientation(original_col_widths, 4)
        adjusted_col_widths = self.adjust_table_for_page(original_col_widths, available_width, min_col_width=2*cm)
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=page_size,
                               rightMargin=2*cm, leftMargin=2*cm,
                               topMargin=3*cm, bottomMargin=2*cm)
        
        story = []
        
        # Titre avec devise
        title_text = f'RÉCAPITULATIF DE STOCK ({currency})'
        story.append(Paragraph(title_text, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*cm))
        
        # Informations (compact)
        info_data = [
            ['Date', self.format_date(datetime.now(UTC)), 'Dépôt', stock_data.get('depot_name', 'Tous les dépôts')],
        ]
        
        info_table = Table(info_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f5f7fa')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.HexColor('#7a8a9a')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (3, 0), (3, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Oblique'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTNAME', (3, 0), (3, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.5*cm))
        
        # Tableau des stocks
        story.append(Paragraph('DÉTAIL DES STOCKS', self.styles['CustomSubtitle']))
        story.append(Spacer(1, 0.2*cm))
        
        headers = ['Article', 'Dépôt', 'Quantité', f'Valeur ({currency})']
        items_data = [headers]
        
        total_value = Decimal('0')
        total_quantity = Decimal('0')
        
        for item in stock_data.get('items', []):
            article_name = item.get('article_name', 'N/A')
            depot_name = item.get('depot_name', 'N/A')
            quantity = item.get('quantity', 0) or 0
            value = item.get('value', 0) or 0
            
            total_value += Decimal(str(value))
            total_quantity += Decimal(str(quantity))
            
            # Limiter la longueur
            max_article_len = int(adjusted_col_widths[0] / 0.3)
            max_depot_len = int(adjusted_col_widths[1] / 0.3)
            article_name = article_name[:max_article_len] if len(article_name) > max_article_len else article_name
            depot_name = depot_name[:max_depot_len] if len(depot_name) > max_depot_len else depot_name
            
            items_data.append([
                article_name,
                depot_name,
                f"{quantity:.2f}",
                self.format_currency(value, currency, exchange_rate).replace(f' {currency}', '')
            ])
        
        # Ligne de total (sans balises HTML)
        items_data.append([
            'TOTAL',
            '',
            f"{total_quantity:.2f}",
            self.format_currency(total_value, currency, exchange_rate).replace(f' {currency}', '')
        ])
        
        items_table = Table(items_data, colWidths=adjusted_col_widths)
        items_table.setStyle(TableStyle([
            # En-têtes
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#003d82')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Données
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.HexColor('#2c3e50')),
            ('ALIGN', (2, 1), (2, -2), 'CENTER'),
            ('ALIGN', (3, 1), (3, -2), 'RIGHT'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
            ('TOPPADDING', (0, 1), (-1, -2), 6),
            # Ligne de total
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f7fa')),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#003d82')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 9),
            ('ALIGN', (2, -1), (-1, -1), 'CENTER'),
            # Grille
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e6ed')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#003d82')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#003d82')),
        ]))
        
        story.append(items_table)
        
        # Générer le PDF
        def header_footer(c, d):
            self.create_header_footer(c, d, 'Récapitulatif de Stock', page_size)
        
        doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
        
        buffer.seek(0)
        return buffer

